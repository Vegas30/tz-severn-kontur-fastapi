from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=120, description="Project title (3-120) chars")
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass 


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=120)
    description: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProjectReadWithOwner(ProjectRead):
    owner_email: Optional[str] = None