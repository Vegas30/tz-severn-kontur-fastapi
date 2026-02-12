from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session, select, func
from fastapi import HTTPException, status

from app.core.audit import log_action
from app.core.permissions import can_edit_project, can_view_project
from app.models.audit_log import EntityType
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.schemas.document_version import DocumentVersionReadWithCreator


class DocumentService:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, doc_id: int) -> Optional[Document]:
        return self.session.get(Document, doc_id)
    
    def _check_project_exists(self, project_id: int) -> Project:
        project = self.session.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return project
    

    def _check_document_exists(self, doc_id: int) -> Document:
        document = self.get_by_id(doc_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    
    def _check_edit_permission(self, user: User, project_id: int) -> None:
        if not can_edit_project(self.session, user, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Editor access required"
            )
        
    def _check_view_permission(self, user: User, project_id: int) -> None:
        """Check view permission on project."""
        if not can_view_project(self.session, user, project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project"
            )

    def create_document(self, project_id: int, doc_data: DocumentCreate,  user: User) -> Document:
        self._check_project_exists(project_id)
        self._check_edit_permission(user, project_id)

        document = Document(
            project_id=project_id,
            title=doc_data.title,
            content=doc_data.content or "",
            status=DocumentStatus.draft,
            created_by=user.id,
            updated_by=user.id
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        version = DocumentVersion(
            document_id=document.id,
            version=1,
            content_snapshot=document.content,
            created_by=user.id
        )
        self.session.add(version)
        self.session.commit()

        log_action(
            session=self.session,
            user_id=user.id,
            action="create_document",
            entity_type=EntityType.document,
            entity_id=document.id,
            meta={"title": document.title, "project_id": project_id}
        )
        
        return document


    def list_documents(self, project_id: int, user: User, skip: int = 0, limit: int = 20) -> list[Document]:
        self._check_project_exists(project_id)
        self._check_view_permission(user, project_id)

        statement = select(Document).where(
            Document.project_id == project_id
        ).offset(skip).limit(limit)
        return list(self.session.exec(statement).all())
    

    def get_document(self, doc_id: int, user: User) -> Document:
        document = self._check_document_exists(doc_id)
        self._check_view_permission(user, document.project_id)
        return document
    
    def update_document(self, doc_id: int, doc_data: DocumentUpdate, user: User) -> Document:
        document = self._check_document_exists(doc_id)
        self._check_edit_permission(user, document.project_id)
        
        update_data = doc_data.model_dump(exclude_unset=True)
        content_changed = False

        if "content" in update_data and update_data["content"] != document.content:
            content_changed = True

        for key, value in update_data.items():
            setattr(document, key, value)
        
        document.updated_by = user.id
        document.updated_at = datetime.now(timezone.utc)
        
        self.session.add(document)
        self.session.commit()

        if content_changed:
            max_version = self._get_max_version(doc_id)
            version = DocumentVersion(
                document_id=doc_id,
                version=max_version + 1,
                content_snapshot=document.content,
                created_by=user.id
            )
            self.session.add(version)
            self.session.commit()
        
        self.session.refresh(document)

        log_action(
            session=self.session,
            user_id=user.id,
            action="update_document",
            entity_type=EntityType.document,
            entity_id=doc_id,
            meta={
                "updated_fields": list(update_data.keys()),
                "content_changed": content_changed
            }
        )
        
        return document
    

    def _get_max_version(self, doc_id: int) -> int:
        statement = select(func.max(DocumentVersion.version)).where(
            DocumentVersion.document_id == doc_id
        )
        return self.session.exec(statement).first() or 0


        #5 записей где среди внешний ключей
        #  мы находим doc_id (конкретный документ который мы ищем в сущности)

        #среди найденных 5 записей функция max находит максимальное значние 
        # из всех полей .version 
        #5 or 0 

        # SELECT MAX(version) 
        # FROM document_versions 
        # WHERE document_id == doc_id

    
    def change_status(self, doc_id: int, new_status: DocumentStatus, user: User) -> Document:
        document = self._check_document_exists(doc_id)
        self._check_edit_permission(user, document.project_id)

        old_status = document.status
        document.status = new_status
        document.updated_by = user.id
        document.updated_at = datetime.now(timezone.utc)
        
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)


        action_name = f"{new_status.value}_document"
        log_action(
            session=self.session,
            user_id=user.id,
            action=action_name,
            entity_type=EntityType.document,
            entity_id=doc_id,
            meta={"old_status": old_status.value, "new_status": new_status.value}
        )
        
        return document
    
    def list_versions(self, doc_id: int, user: User) -> list[DocumentVersionReadWithCreator]:
        document = self._check_document_exists(doc_id)
        self._check_view_permission(user, document.project_id)
        
        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == doc_id
        ).order_by(DocumentVersion.version.desc())
        versions = self.session.exec(statement).all()


        result = []
        for ver in versions:
            creator = self.session.get(User, ver.created_by)
            result.append(DocumentVersionReadWithCreator(
                id=ver.id,
                document_id=ver.document_id,
                version=ver.version,
                content_snapshot=ver.content_snapshot,
                created_by=ver.created_by,
                created_at=ver.created_at,
                creator_email=creator.email if creator else None
            ))
        
        return result
    

    def get_version(self, doc_id: int, version: int, user: User) -> DocumentVersion:
        document = self._check_document_exists(doc_id)
        self._check_view_permission(user, document.project_id)
        
        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == doc_id,
            DocumentVersion.version == version
        )
        ver = self.session.exec(statement).first()
        
        if not ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return ver
    
    def restore_version(self, doc_id: int, version: int, user: User) -> Document:
        document = self._check_document_exists(doc_id)
        self._check_edit_permission(user, document.project_id)

        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == doc_id,
            DocumentVersion.version == version
        )
        ver = self.session.exec(statement).first()
        
        if not ver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        document.content = ver.content_snapshot
        document.updated_by = user.id
        document.updated_at = datetime.now(timezone.utc)
        
        self.session.add(document)
        self.session.commit()

        max_version = self._get_max_version(doc_id)
        new_version = DocumentVersion(
            document_id=doc_id,
            version=max_version + 1,
            content_snapshot=document.content,
            created_by=user.id
        )
        self.session.add(new_version)
        self.session.commit()
        self.session.refresh(document)

        log_action(
            session=self.session,
            user_id=user.id,
            action="restore_version",
            entity_type=EntityType.document,
            entity_id=doc_id,
            meta={"restored_version": version, "new_version": max_version + 1}
        )
        
        return document
