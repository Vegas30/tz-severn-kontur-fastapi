from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

from app.models.audit_log import EntityType


class AuditLogBase(BaseModel):
    action: str
    entity_type: EntityType
    entity_id: Optional[int] = None
    meta: Optional[str] = None


class AuditLogCreate(AuditLogBase):
        user_id: int


class AuditLogRead(AuditLogBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogReadWithUser(AuditLogRead):
     user_email: Optional[str] = None


class AuditLogFilter(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[EntityType] = None


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
