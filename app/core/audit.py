import json 
from typing import Optional, Any 
from sqlmodel import Session

from app.models.audit_log import AuditLog, EntityType


def log_action(session: Session, 
               user_id: int, 
               action: str, 
               entity_type: EntityType, entity_id: Optional[int]=None, 
               meta:Optional[dict[str, Any]]=None) -> AuditLog:
    
    meta_str = json.dumps(meta) if meta else None

    audit_log = AuditLog(
        user_id = user_id, 
        action=action,
        entity_type = entity_type,
        entity_id=entity_id,
        meta=meta_str
    )

    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)
    return audit_log

