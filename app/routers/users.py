from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session

from app.core.security import require_admin
from app.db.session import get_session
from app.schemas.user import UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(session)

@router.get("/", response_model=list[UserRead])
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=500),
    is_admin: bool = Depends(require_admin),
    service: UserService = Depends(get_user_service)
):
    if not is_admin: 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return service.list_users(skip=skip, limit=limit)