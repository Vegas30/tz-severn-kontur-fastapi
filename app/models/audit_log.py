from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship

class EntityType(str, Enum):
    user = "user"
    project = "project"
    document = "document"
    access = "access"

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    action: str = Field(max_length=100)
    entity_type: EntityType
    entity_id: Optional[int] = Field(default=None)
    meta: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc), index=True)

