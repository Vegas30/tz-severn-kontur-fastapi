from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from app.schemas.token import Token


from app.core.security import get_current_user, require_admin
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    is_admin: bool = Depends(require_admin),
    current_user: User = Depends(get_current_user)
):
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    service = UserService(session)
    return service.create_user(user_data, current_user)


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    session: Session = Depends(get_session)
):
    service = UserService(session)
    return service.authenticate(credentials)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user