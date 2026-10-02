from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Connection, text

from app.application.numbering import allocate_document_number
from app.domain.security import RequestContext, require_permission
from app.infrastructure.platform import write_audit, write_outbox

ZERO = Decimal(0)


class FinanceError(ValueError):
    pass


class FiscalPeriodClosed(FinanceError):
    pass


class UnbalancedJournal(FinanceError):
    pass


def create_account(db: Connection, *, context: RequestContext, legal_entity_id: UUID, code: str,
                   name: str, account_type: str, currency_code: str | None = None,
                   is_control: bool = False) -> UUID:
    require_permission(context, "accounting.configure")
    entity = db.execute(text("SELECT 1 FROM legal_entities WHERE tenant_id=:t AND id=:e AND status='ACTIVE'"),
                        {"t": context.tenant_id, "e": legal_entity_id}).scalar_one_or_none()
    if not entity:
        raise FinanceError("legal entity not found")
    account_id = uuid4()
    db.execute(text("""INSERT INTO finance_accounts
      (id,tenant_id,legal_entity_id,code,name,account_type,currency_code,is_control,status,created_at,updated_at)
      VALUES (:id,:t,:e,:code,:name,:type,:currency,:control,'ACTIVE',now(),now())"""),
      {"id": account_id, "t": context.tenant_id, "e": legal_entity_id, "code": code,
       "name": name, "type": account_type, "currency": currency_code, "control": is_control})
    write_audit(db, tenant_id=context.tenant_id, request_id=context.request_id,
                action="finance.account.created", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="finance_account",
                target_id=account_id, metadata={"code": code, "legal_entity_id": str(legal_entity_id)})
    return account_id


def create_fiscal_period(db: Connection, *, context: RequestContext, legal_entity_id: UUID,
                         period_key: str, start_date: date, end_date: date) -> UUID:
    require_permission(context, "accounting.configure")
    if end_date < start_date:
        raise FinanceError("invalid fiscal period dates")
    overlap = db.execute(text("""SELECT 1 FROM fiscal_periods WHERE tenant_id=:t AND legal_entity_id=:e
      AND daterange(start_date,end_date,'[]') && daterange(:start,:end,'[]')"""),
      {"t": context.tenant_id, "e": legal_entity_id, "start": start_date, "end": end_date}).first()
    if overlap:
        raise FinanceError("fiscal period overlaps existing period")
    period_id = uuid4()
    db.execute(text("""INSERT INTO fiscal_periods
      (id,tenant_id,legal_entity_id,period_key,start_date,end_date,status,created_at,updated_at)
      VALUES (:id,:t,:e,:key,:start,:end,'OPEN',now(),now())"""),
      {"id": period_id, "t": context.tenant_id, "e": legal_entity_id, "key": period_key,
       "start": start_date, "end": end_date})
    return period_id


def set_fiscal_period_status(db: Connection, *, context: RequestContext, period_id: UUID,
                             status: str) -> None:
    if status == "CLOSED":
        require_permission(context, "fiscal_period.close")
    elif status == "OPEN":
        require_permission(context, "fiscal_period.reopen")
    else:
        raise FinanceError("unsupported fiscal period transition")
    row = db.execute(text("""SELECT status FROM fiscal_periods WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
                     {"t": context.tenant_id, "id": period_id}).scalar_one_or_none()
    if row is None:
        raise FinanceError("fiscal period not found")
    if row == status:
        return
    db.execute(text("""UPDATE fiscal_periods SET status=:status,closed_at=:closed,updated_at=now()
      WHERE tenant_id=:t AND id=:id"""), {"status": status,
      "closed": datetime.now(UTC) if status == "CLOSED" else None, "t": context.tenant_id, "id": period_id})
    write_audit(db, tenant_id=context.tenant_id, request_id=context.request_id,
                action=f"finance.fiscal_period.{'closed' if status == 'CLOSED' else 'reopened'}",
                actor_user_id=context.actor_user_id, actor_tenant_user_id=context.tenant_user_id,
                target_type="fiscal_period", target_id=period_id, metadata={})


def _open_period(db: Connection, tenant: UUID, entity: UUID, posting_date: date) -> None:
    status = db.execute(text("""SELECT status FROM fiscal_periods WHERE tenant_id=:t AND legal_entity_id=:e
      AND :d BETWEEN start_date AND end_date FOR UPDATE"""),
      {"t": tenant, "e": entity, "d": posting_date}).scalar_one_or_none()
    if status != "OPEN":
        raise FiscalPeriodClosed("posting date is not in an open fiscal period")


def post_journal(db: Connection, *, context: RequestContext, legal_entity_id: UUID, posting_date: date,
                 currency_code: str, description: str, source_module: str, source_type: str,
                 source_id: UUID, source_number: str | None, source_effect: str, idempotency_key: str,
                 period_key: str, lines: list[dict[str, object]], permission: str = "journal.post") -> UUID:
    require_permission(context, permission)
    replay = db.execute(text("SELECT id FROM journal_entries WHERE tenant_id=:t AND idempotency_key=:key"),
                        {"t": context.tenant_id, "key": idempotency_key}).scalar_one_or_none()
    if replay:
        return replay
    if len(lines) < 2:
        raise UnbalancedJournal("journal requires at least two lines")
    debit = sum((Decimal(str(line.get("debit", 0))) for line in lines), ZERO)
    credit = sum((Decimal(str(line.get("credit", 0))) for line in lines), ZERO)
    if debit <= ZERO or debit != credit:
        raise UnbalancedJournal("journal debit and credit must balance")
    _open_period(db, context.tenant_id, legal_entity_id, posting_date)
    account_ids = [UUID(str(line["account_id"])) for line in lines]
    owned = db.execute(text("""SELECT count(*) FROM finance_accounts WHERE tenant_id=:t AND legal_entity_id=:e
      AND id = ANY(:ids) AND status='ACTIVE'"""), {"t": context.tenant_id, "e": legal_entity_id,
      "ids": account_ids}).scalar_one()
    if owned != len(set(account_ids)):
        raise FinanceError("journal account is outside legal entity or inactive")
    number = allocate_document_number(db, tenant_id=context.tenant_id, document_type="JV",
                                      period_key=period_key, legal_entity_id=legal_entity_id)
    journal_id, now = uuid4(), datetime.now(UTC)
    db.execute(text("""INSERT INTO journal_entries
      (id,tenant_id,legal_entity_id,journal_number,posting_date,currency_code,exchange_rate,description,
       source_module,source_type,source_id,source_number,source_effect,idempotency_key,status,
       created_by_tenant_user_id,posted_at,created_at)
      VALUES (:id,:t,:e,:number,:date,:currency,1,:description,:module,:type,:source,:source_number,
       :effect,:key,'POSTED',:actor,:now,:now)"""), {"id": journal_id, "t": context.tenant_id,
       "e": legal_entity_id, "number": number, "date": posting_date, "currency": currency_code,
       "description": description, "module": source_module, "type": source_type, "source": source_id,
       "source_number": source_number, "effect": source_effect, "key": idempotency_key,
       "actor": context.tenant_user_id, "now": now})
    for index, line in enumerate(lines, 1):
        d, c = Decimal(str(line.get("debit", 0))), Decimal(str(line.get("credit", 0)))
        db.execute(text("""INSERT INTO journal_lines
          (id,tenant_id,journal_entry_id,line_number,account_id,description,debit,credit,base_debit,base_credit)
          VALUES (:id,:t,:journal,:n,:account,:description,:debit,:credit,:debit,:credit)"""),
          {"id": uuid4(), "t": context.tenant_id, "journal": journal_id, "n": index,
           "account": line["account_id"], "description": line.get("description"), "debit": d, "credit": c})
    write_audit(db, tenant_id=context.tenant_id, request_id=context.request_id,
                action="finance.journal.posted", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="journal_entry",
                target_id=journal_id, metadata={"debit": str(debit), "credit": str(credit),
                                                "source_type": source_type, "source_id": str(source_id)})
    write_outbox(db, tenant_id=context.tenant_id, aggregate_type="journal_entry", aggregate_id=journal_id,
                 event_type="finance.journal.posted", payload={"journal_id": str(journal_id)})
    return journal_id


def reverse_journal(db: Connection, *, context: RequestContext, journal_id: UUID,
                    posting_date: date, period_key: str, idempotency_key: str) -> UUID:
    require_permission(context, "journal.reverse")
    row = db.execute(text("""SELECT * FROM journal_entries WHERE tenant_id=:t AND id=:id FOR UPDATE"""),
                     {"t": context.tenant_id, "id": journal_id}).mappings().first()
    if not row or row["status"] != "POSTED":
        raise FinanceError("journal is not reversible")
    lines = db.execute(text("""SELECT account_id,description,credit debit,debit credit FROM journal_lines
      WHERE tenant_id=:t AND journal_entry_id=:id ORDER BY line_number"""),
      {"t": context.tenant_id, "id": journal_id}).mappings().all()
    reversal = post_journal(db, context=context, legal_entity_id=row["legal_entity_id"], posting_date=posting_date,
        currency_code=row["currency_code"], description=f"Reversal of {row['journal_number']}",
        source_module="FINANCE", source_type="JOURNAL_REVERSAL", source_id=journal_id,
        source_number=row["journal_number"], source_effect="REVERSAL", idempotency_key=idempotency_key,
        period_key=period_key, lines=[dict(x) for x in lines], permission="journal.reverse")
    db.execute(text("UPDATE journal_entries SET status='REVERSED' WHERE tenant_id=:t AND id=:id"),
               {"t": context.tenant_id, "id": journal_id})
    db.execute(text("UPDATE journal_entries SET reversal_of_id=:original WHERE tenant_id=:t AND id=:reversal"),
               {"original": journal_id, "t": context.tenant_id, "reversal": reversal})
    write_audit(db, tenant_id=context.tenant_id, request_id=context.request_id,
                action="finance.journal.reversed", actor_user_id=context.actor_user_id,
                actor_tenant_user_id=context.tenant_user_id, target_type="journal_entry",
                target_id=journal_id, metadata={"reversal_journal_id": str(reversal)})
    return reversal
