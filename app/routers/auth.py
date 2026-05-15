"""Authentication router."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..models_pro import User
from ..schemas_pro import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from ..crud_pro import (
    authenticate_user,
    create_user,
    get_refresh_token,
    revoke_refresh_token,
    save_refresh_token,
)
from ..auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_refresh_token,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user_create = UserCreate(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )
    user = create_user(db, user_create)
    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return tokens."""
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    save_refresh_token(db, user.id, jti, datetime.utcnow() + settings.refresh_token_expire)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using a refresh token."""
    token_data = verify_refresh_token(payload.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id, jti = token_data
    refresh_record = get_refresh_token(db, jti)
    if not refresh_record or refresh_record.is_revoked or refresh_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or revoked",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    revoke_refresh_token(db, jti)
    access_token = create_access_token(user.id)
    new_refresh_token, new_jti = create_refresh_token(user.id)
    save_refresh_token(db, user.id, new_jti, datetime.utcnow() + settings.refresh_token_expire)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout and revoke the active refresh token."""
    token_data = verify_refresh_token(payload.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id, jti = token_data
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token does not belong to the authenticated user",
        )

    if not revoke_refresh_token(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already revoked or invalid",
        )

    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)