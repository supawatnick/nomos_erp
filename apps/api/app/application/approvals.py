import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox


class ApprovalError(ValueError):
    pass


class ApprovalStale(ApprovalError):
    pass


def fingerprint_snapshot(snapshot: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def create_policy(
    db: Connection,
    *,
    context: RequestContext,
    code: str,
    name: str,
    request_type: str,
    required_permission: str,
    steps_required: int = 1,
    prohibit_self_approval: bool = True,
    expires_after_hours: int | None = None,
) -> UUID:
    require_permission(context, "approval.policy.manage")
    if steps_required < 1 or (expires_after_hours is not None and expires_after_hours < 1):
        raise ApprovalError("invalid approval policy")
    policy_id, now = uuid4(), datetime.now(UTC)
    db.execute(
        text("""INSERT INTO approval_policies
        (id,tenant_id,code,name,request_type,required_permission,steps_required,
         prohibit_self_approval,expires_after_hours,status,created_at,updated_at)
        VALUES (:id,:tenant,:code,:name,:type,:permission,:steps,:self,:expiry,'ACTIVE',:now,:now)"""),
        {"id": policy_id, "tenant": context.tenant_id, "code": code, "name": name,
         "type": request_type, "permission": required_permission, "steps": steps_required,
         "self": prohibit_self_approval, "expiry": expires_after_hours, "now": now},
    )
    write_audit(
        db, tenant_id=context.tenant_id, request_id=context.request_id,
        action="approval.policy.created", actor_user_id=context.actor_user_id,
        actor_tenant_user_id=context.tenant_user_id, target_type="approval_policy",
        target_id=policy_id, metadata={"code": code, "request_type": request_type},
    )
    return policy_id


def request_approval(
    db: Connection,
    *,
    context: RequestContext,
    policy_code: str,
    source_type: str,
    source_id: UUID,
    source_version: int | None,
    snapshot: dict[str, object],
) -> UUID:
    require_permission(context, "approval.request")
    policy = db.execute(
        text("""SELECT id,request_type,expires_after_hours FROM approval_policies
        WHERE tenant_id=:tenant AND code=:code AND status='ACTIVE'"""),
        {"tenant": context.tenant_id, "code": policy_code},
    ).mappings().first()
    if not policy:
        raise ApprovalError("active approval policy not found")
    now = datetime.now(UTC)
    expires_at = (
        now + timedelta(hours=int(policy["expires_after_hours"]))
        if policy["expires_after_hours"] is not None else None
    )
    request_id = uuid4()
    db.execute(
        text("""INSERT INTO approval_requests
        (id,tenant_id,policy_id,request_type,source_type,source_id,source_version,
         source_fingerprint,request_snapshot,status,requester_tenant_user_id,current_step,
         expires_at,created_at,updated_at)
        VALUES (:id,:tenant,:policy,:type,:source_type,:source_id,:version,:fingerprint,
                CAST(:snapshot AS JSONB),'PENDING',:requester,1,:expires,:now,:now)"""),
        {"id": request_id, "tenant": context.tenant_id, "policy": policy["id"],
         "type": policy["request_type"], "source_type": source_type, "source_id": source_id,
         "version": source_version, "fingerprint": fingerprint_snapshot(snapshot),
         "snapshot": json.dumps(snapshot, default=str), "requester": context.tenant_user_id,
         "expires": expires_at, "now": now},
    )
    write_audit(
        db, tenant_id=context.tenant_id, request_id=context.request_id,
        action="approval.request.created", actor_user_id=context.actor_user_id,
        actor_tenant_user_id=context.tenant_user_id, target_type="approval_request",
        target_id=request_id, metadata={"policy_code": policy_code, "source_type": source_type,
                                        "source_id": str(source_id)},
    )
    write_outbox(
        db, tenant_id=context.tenant_id, aggregate_type="approval_request",
        aggregate_id=request_id, event_type="approval.request.created",
        payload={"approval_request_id": str(request_id), "source_type": source_type,
                 "source_id": str(source_id)},
    )
    return request_id


def decide_approval(
    db: Connection,
    *,
    context: RequestContext,
    approval_request_id: UUID,
    decision: str,
    idempotency_key: str,
    reason: str | None = None,
) -> str:
    require_permission(context, "approval.decide")
    decision = decision.upper()
    if decision not in {"APPROVED", "REJECTED"}:
        raise ApprovalError("invalid approval decision")
    row = db.execute(
        text("""SELECT r.status,r.requester_tenant_user_id,r.current_step,r.expires_at,
                      p.steps_required,p.prohibit_self_approval,p.required_permission
        FROM approval_requests r JOIN approval_policies p
          ON p.tenant_id=r.tenant_id AND p.id=r.policy_id
        WHERE r.tenant_id=:tenant AND r.id=:id FOR UPDATE OF r"""),
        {"tenant": context.tenant_id, "id": approval_request_id},
    ).mappings().first()
    if not row:
        raise ApprovalError("approval request not found")
    replay = db.execute(
        text("""SELECT decision FROM approval_decisions
        WHERE tenant_id=:tenant AND approval_request_id=:id AND idempotency_key=:key"""),
        {"tenant": context.tenant_id, "id": approval_request_id, "key": idempotency_key},
    ).scalar_one_or_none()
    if replay is not None:
        return str(replay)
    now = datetime.now(UTC)
    if row["status"] != "PENDING":
        raise ApprovalError("approval request is not pending")
    if row["expires_at"] is not None and row["expires_at"] <= now:
        db.execute(
            text("""UPDATE approval_requests SET status='EXPIRED',updated_at=:now
            WHERE tenant_id=:tenant AND id=:id"""),
            {"now": now, "tenant": context.tenant_id, "id": approval_request_id},
        )
        raise ApprovalError("approval request expired")
    require_permission(context, str(row["required_permission"]))
    if row["prohibit_self_approval"] and row["requester_tenant_user_id"] == context.tenant_user_id:
        raise ApprovalError("self approval is prohibited")
    step = int(row["current_step"])
    db.execute(
        text("""INSERT INTO approval_decisions
        (id,tenant_id,approval_request_id,step_number,decided_by_tenant_user_id,
         decision,reason,idempotency_key,decided_at)
        VALUES (:id,:tenant,:request,:step,:actor,:decision,:reason,:key,:now)"""),
        {"id": uuid4(), "tenant": context.tenant_id, "request": approval_request_id,
         "step": step, "actor": context.tenant_user_id, "decision": decision,
         "reason": reason, "key": idempotency_key, "now": now},
    )
    if decision == "REJECTED":
        new_status, next_step = "REJECTED", step
    elif step >= int(row["steps_required"]):
        new_status, next_step = "APPROVED", step
    else:
        new_status, next_step = "PENDING", step + 1
    db.execute(
        text("""UPDATE approval_requests
        SET status=:status,current_step=:step,approved_at=:approved,updated_at=:now
        WHERE tenant_id=:tenant AND id=:id"""),
        {"status": new_status, "step": next_step,
         "approved": now if new_status == "APPROVED" else None, "now": now,
         "tenant": context.tenant_id, "id": approval_request_id},
    )
    write_audit(
        db, tenant_id=context.tenant_id, request_id=context.request_id,
        action=f"approval.request.{decision.lower()}", actor_user_id=context.actor_user_id,
        actor_tenant_user_id=context.tenant_user_id, target_type="approval_request",
        target_id=approval_request_id, metadata={"step": step, "reason": reason},
    )
    return decision


def cancel_approval(
    db: Connection, *, context: RequestContext, approval_request_id: UUID
) -> None:
    require_permission(context, "approval.request")
    row = db.execute(
        text("""SELECT status,requester_tenant_user_id FROM approval_requests
        WHERE tenant_id=:tenant AND id=:id FOR UPDATE"""),
        {"tenant": context.tenant_id, "id": approval_request_id},
    ).mappings().first()
    if not row:
        raise ApprovalError("approval request not found")
    if row["requester_tenant_user_id"] != context.tenant_user_id:
        raise ApprovalError("only requester can cancel approval")
    if row["status"] != "PENDING":
        raise ApprovalError("only pending approval can be cancelled")
    db.execute(
        text("""UPDATE approval_requests SET status='CANCELLED',updated_at=:now
        WHERE tenant_id=:tenant AND id=:id"""),
        {"now": datetime.now(UTC), "tenant": context.tenant_id, "id": approval_request_id},
    )


def require_approved_snapshot(
    db: Connection,
    *,
    context: RequestContext,
    approval_request_id: UUID,
    source_type: str,
    source_id: UUID,
    source_version: int | None,
    snapshot: dict[str, object],
) -> None:
    row = db.execute(
        text("""SELECT status,source_type,source_id,source_version,source_fingerprint,expires_at
        FROM approval_requests WHERE tenant_id=:tenant AND id=:id FOR UPDATE"""),
        {"tenant": context.tenant_id, "id": approval_request_id},
    ).mappings().first()
    if not row or row["status"] != "APPROVED":
        raise ApprovalError("approval is not approved")
    if row["expires_at"] is not None and row["expires_at"] <= datetime.now(UTC):
        raise ApprovalStale("approval expired")
    if row["source_type"] != source_type or row["source_id"] != source_id:
        raise ApprovalStale("approval source mismatch")
    if row["source_version"] != source_version:
        raise ApprovalStale("approval source version changed")
    if row["source_fingerprint"] != fingerprint_snapshot(snapshot):
        raise ApprovalStale("approval source changed")


def mark_executed(
    db: Connection,
    *,
    context: RequestContext,
    approval_request_id: UUID,
    execution_reference: str,
) -> None:
    result = db.execute(
        text("""UPDATE approval_requests SET status='EXECUTED',executed_at=:now,
        execution_reference=:reference,updated_at=:now
        WHERE tenant_id=:tenant AND id=:id AND status='APPROVED'"""),
        {"now": datetime.now(UTC), "reference": execution_reference,
         "tenant": context.tenant_id, "id": approval_request_id},
    )
    if result.rowcount != 1:
        raise ApprovalError("approved request cannot be executed")
    write_audit(
        db, tenant_id=context.tenant_id, request_id=context.request_id,
        action="approval.request.executed", actor_user_id=context.actor_user_id,
        actor_tenant_user_id=context.tenant_user_id, target_type="approval_request",
        target_id=approval_request_id, metadata={"execution_reference": execution_reference},
    )
