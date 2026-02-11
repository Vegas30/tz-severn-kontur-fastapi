from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session
from typing import List

from app.core.security import get_current_user
from app.db.session import get_session
from app.models.document import DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead, DocumentUpdate
from app.schemas.document_version import DocumentVersionRead, DocumentVersionReadWithCreator
from app.services.document_service import DocumentService


router = APIRouter(tags=["Documents"])

@router.post("/projects/{project_id}/documents",  response_model=DocumentRead,  status_code=status.HTTP_201_CREATED)
def create_document(project_id: int, doc_data: DocumentCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.create_document(project_id, doc_data, current_user)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
def list_documents(
    project_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.list_documents(project_id, current_user, skip, limit)


@router.get("/documents/{doc_id}", response_model=DocumentRead)
def get_document(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.get_document(doc_id, current_user)



@router.patch("/documents/{doc_id}", response_model=DocumentRead)
def update_document(
    doc_id: int,
    doc_data: DocumentUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.update_document(doc_id, doc_data, current_user)


@router.post("/documents/{doc_id}/publish", response_model=DocumentRead)
def publish_document(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.change_status(doc_id, DocumentStatus.published, current_user)


@router.post("/documents/{doc_id}/archive", response_model=DocumentRead)
def archive_document(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.change_status(doc_id, DocumentStatus.archived, current_user)


@router.get("/documents/{doc_id}/versions", response_model=List[DocumentVersionReadWithCreator])
def list_document_versions(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.list_versions(doc_id, current_user)


@router.get("/documents/{doc_id}/versions/{version}", response_model=DocumentVersionRead)
def get_document_version(
    doc_id: int,
    version: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.get_version(doc_id, version, current_user)


@router.post("/documents/{doc_id}/versions/{version}/restore", response_model=DocumentRead)
def restore_document_version(
    doc_id: int,
    version: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = DocumentService(session)
    return service.restore_version(doc_id, version, current_user)
