from typing import Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.core.audit import log_action
from app.core.permissions import can_manage_project
from app.models.audit_log import EntityType
from app.models.project import Project
from app.models.project_access import ProjectAccess
from app.models.user import User
from app.schemas.project_access import ProjectAccessCreate, ProjectAccessReadWithUser

class AccessService:
    def __init__(self, session: Session):
        self.session = session
    
    def _check_project_exists(self, project_id: int) -> Project:
        project = self.session.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return project
    
    def _check_user_exists(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found"
            )
        return user
    
    def _check_manage_permission(self, user: User, project_id: int) -> None:
        """Check if user can manage project access."""
        if not can_manage_project(self.session, user, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin or project owner can manage access"
            )
        
    def get_access(self, project_id: int, user_id: int) -> Optional[ProjectAccess]:
        statement = select(ProjectAccess).where(
            ProjectAccess.project_id == project_id,
            ProjectAccess.user_id == user_id
        )
        return self.session.exec(statement).first()
        
    def grant_access(self, project_id: int, access_data: ProjectAccessCreate, granted_by: User) -> ProjectAccessReadWithUser:
        self._check_project_exists(project_id)
        self._check_manage_permission(granted_by, project_id)
        target_user = self._check_user_exists(access_data.user_id)

        existing_access = self.get_access(project_id, access_data.user_id)

        if existing_access:
            existing_access.permission = access_data.permission
            existing_access.granted_by = granted_by.id
            self.session.add(existing_access)
            self.session.commit()
            self.session.refresh(existing_access)
            access = existing_access
            action = "update_access"

        else:
            # Create new access
            access = ProjectAccess(
                project_id=project_id,
                user_id=access_data.user_id,
                permission=access_data.permission,
                granted_by=granted_by.id
            )
            self.session.add(access)
            self.session.commit()
            self.session.refresh(access)
            action = "grant_access"

        log_action(
            session=self.session,
            user_id=granted_by.id,
            action=action,
            entity_type=EntityType.access,
            entity_id=access.id,
            meta={
                "project_id": project_id,
                "target_user_id": access_data.user_id,
                "permission": access_data.permission.value
            }
        )
        
        return ProjectAccessReadWithUser(
            id=access.id,
            project_id=access.project_id,
            user_id=access.user_id,
            permission=access.permission,
            granted_by=access.granted_by,
            created_at=access.created_at,
            user_email=target_user.email,
            granter_email=granted_by.email
        )


    def revoke_access(self, project_id: int, user_id: int, revoked_by: User) -> None:
        self._check_project_exists(project_id)
        self._check_manage_permission(revoked_by, project_id)
        
        access = self.get_access(project_id, user_id)
        if not access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access not found"
            )
        
        access_id = access.id
        self.session.delete(access)
        self.session.commit()

        log_action(
            session=self.session,
            user_id=revoked_by.id,
            action="revoke_access",
            entity_type=EntityType.access,
            entity_id=access_id,
            meta={
                "project_id": project_id,
                "target_user_id": user_id
            }
        )

    def list_project_access(self, project_id: int, user: User) -> list[ProjectAccessReadWithUser]:
        self._check_project_exists(project_id)
        self._check_manage_permission(user, project_id)
        
        statement = select(ProjectAccess).where(ProjectAccess.project_id == project_id)
        accesses = self.session.exec(statement).all()

        result = []
        for access in accesses:
            target_user = self.session.get(User, access.user_id)
            granter = self.session.get(User, access.granted_by)
            result.append(ProjectAccessReadWithUser(
                id=access.id,
                project_id=access.project_id,
                user_id=access.user_id,
                permission=access.permission,
                granted_by=access.granted_by,
                created_at=access.created_at,
                user_email=target_user.email if target_user else None,
                granter_email=granter.email if granter else None
            ))
        
        return result

    
