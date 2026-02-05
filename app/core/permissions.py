from typing import Optional
from sqlmodel import Session, select

from app.models.project import Project
from app.models.project_access import Permission, ProjectAccess
from app.models.user import User, UserRole

def get_user_project_permission(session: Session, user: User, project_id: int) -> Optional[Permission]:
    if user.role == UserRole.admin:
        return Permission.editor
    
    project = session.get(Project, project_id)
    if project and project.owner_id == user.id:
        return Permission.editor
    
    statement = select(ProjectAccess).where(
        ProjectAccess.project_id == project_id,
        ProjectAccess.user_id == user.id
    )
    access = session.exec(statement).first()
    
    if access:
        return access.permission
    
    return None


def can_view_project(session: Session, user: User, project_id: int) -> bool:
    permission = get_user_project_permission(session, user, project_id)
    return permission is not None

def is_project_owner_or_admin(session: Session, user: User, project_id: int) -> bool:
    if user.role == UserRole.admin:
        return True
    
    project = session.get(Project, project_id)
    return project is not None and project.owner_id == user.id

def can_manage_project(session: Session, user: User, project_id: int) -> bool:
    return is_project_owner_or_admin(session, user, project_id)