from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

from app.application.auth import resolve_session
from app.application.imports import ImportError, commit_batch, create_batch, validate_batch
from app.core.config import get_settings
from app.domain.security import RequestContext

router=APIRouter(prefix="/api/v1/imports",tags=["imports"])


class ImportCreate(BaseModel):
    import_type:str
    source_name:str=Field(min_length=1,max_length=240)
    rows:list[dict[str,Any]]=Field(min_length=1,max_length=5000)


def _context(request:Request,authorization:str|None,tenant:str|None)->RequestContext:
    if not authorization or not authorization.startswith("Bearer ") or not tenant:
        raise HTTPException(status_code=401,detail={"code":"AUTHENTICATION_REQUIRED"})
    try:return resolve_session(authorization.removeprefix("Bearer ").strip(),UUID(tenant),request.state.request_id)
    except (ValueError,TypeError) as exc:raise HTTPException(status_code=401,detail={"code":"AUTHENTICATION_REQUIRED"}) from exc


@router.post("",status_code=201)
def upload(payload:ImportCreate,request:Request,authorization:str|None=Header(default=None),
           x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:batch=create_batch(db,context=context,import_type=payload.import_type,source_name=payload.source_name,rows=payload.rows)
    except ImportError as exc:raise HTTPException(status_code=422,detail={"code":"VALIDATION_FAILED","message":str(exc)}) from exc
    return {"data":{"id":str(batch),"status":"UPLOADED"},"meta":{"request_id":str(context.request_id)}}


@router.post("/{batch_id}/validate")
def validate(batch_id:UUID,request:Request,authorization:str|None=Header(default=None),
             x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:counts=validate_batch(db,context=context,batch_id=batch_id)
    except ImportError as exc:raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(batch_id),**counts},"meta":{"request_id":str(context.request_id)}}


@router.post("/{batch_id}/commit")
def commit(batch_id:UUID,request:Request,authorization:str|None=Header(default=None),
           x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    try:
        with engine.begin() as db:targets=commit_batch(db,context=context,batch_id=batch_id)
    except (ImportError,ValueError) as exc:raise HTTPException(status_code=409,detail={"code":"INVALID_DOCUMENT_STATE","message":str(exc)}) from exc
    return {"data":{"id":str(batch_id),"status":"COMMITTED","targets":[str(x) for x in targets]},"meta":{"request_id":str(context.request_id)}}


@router.get("/{batch_id}")
def detail(batch_id:UUID,request:Request,authorization:str|None=Header(default=None),
           x_tenant_id:str|None=Header(default=None,alias="X-Tenant-ID"))->dict[str,object]:
    context=_context(request,authorization,x_tenant_id);engine=create_engine(get_settings().database_url,pool_pre_ping=True)
    with engine.connect() as db:
        head=db.execute(text("SELECT id,import_type,status,source_name,total_rows,valid_rows,error_rows,committed_transaction_id FROM import_batches WHERE tenant_id=:t AND id=:id"),
                        {"t":context.tenant_id,"id":batch_id}).mappings().first()
        if not head:raise HTTPException(status_code=404,detail={"code":"RESOURCE_NOT_FOUND"})
        rows=db.execute(text("SELECT row_number,source_data,normalized_data,errors,target_id FROM import_rows WHERE tenant_id=:t AND batch_id=:id ORDER BY row_number"),
                        {"t":context.tenant_id,"id":batch_id}).mappings().all()
    data=dict(head);data["id"]=str(data["id"]);data["committed_transaction_id"]=str(data["committed_transaction_id"]) if data["committed_transaction_id"] else None
    data["rows"]=[{**dict(x),"target_id":str(x["target_id"]) if x["target_id"] else None} for x in rows]
    return {"data":data,"meta":{"request_id":str(context.request_id)}}
