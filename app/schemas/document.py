from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.models.document import DocumentStatus

class DocumentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=120, description="Document title (3-120 chars)")
    content: Optional[str] = ""


class DocumentCreate(DocumentBase):
    pass 


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=120)
    content: Optional[str] = None


class DocumentRead(DocumentBase):
    id: int
    project_id: int
    status: DocumentStatus
    created_by: int
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentReadWithDetails(DocumentRead):
    creator_email: Optional[str] = None
    updater_email: Optional[str] = None
    version_count: int = 0
