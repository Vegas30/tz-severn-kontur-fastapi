from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.security import require_admin
from app.db.session import get_session
from app.models.audit_log import AuditLog, EntityType
from app.models.user import User
from app.schemas.audit_log import AuditLogFilter, AuditLogReadWithUser


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditLogReadWithUser])
def list_audit_logs(
    date_from: Optional[date] = Query(default=None, description="Filter from date"),
    date_to: Optional[date] = Query(default=None, description="Filter to date"),
    user_id: Optional[int] = Query(default=None, description="Filter by user ID"),
    action: Optional[str] = Query(default=None, description="Filter by action"),
    entity_type: Optional[EntityType] = Query(default=None, description="Filter by entity type"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    statement = select(AuditLogFilter)

    if date_from:
        dt_from = datetime.combine(date_from, datetime.min.time())
        statement = statement.where(AuditLog.created_at >= dt_from)

    if date_to:
        dt_to = datetime.combine(date_to, datetime.max.time())
        statement = statement.where(AuditLog.created_at <= dt_to)

    if user_id:
        statement = statement.where(AuditLog.user_id == user_id)
    
    if action:
        statement = statement.where(AuditLog.action == action)
    
    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)
    
    
    statement = statement.order_by(AuditLog.created_at.desc())
    statement = statement.offset(skip).limit(limit)

    logs = session.exec(statement).all()


    result = []
    for log in logs:
        user = session.get(User, log.user_id)
        result.append(AuditLogReadWithUser(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            meta=log.meta,
            created_at=log.created_at,
            user_email=user.email if user else None
        ))
    
    return result

