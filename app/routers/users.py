"""User management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..auth import get_current_user
from ..models_pro import UserRoleEnum
from .. import crud_pro
from ..schemas_pro import (
    UserCreate, UserUpdate, UserResponse, UserDetailResponse,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    current = crud_pro.get_user(db, current_user)
    if not current or current.role != UserRoleEnum.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    try:
        return crud_pro.create_user(db, user_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user details."""
    user = crud_pro.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current = crud_pro.get_user(db, current_user)
    if current_user != user_id and (not current or current.role != UserRoleEnum.admin):
        raise HTTPException(status_code=403, detail="Access denied")

    return user


@router.get("", response_model=list[UserResponse])
async def get_users_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users."""
    users, _ = crud_pro.get_users(db, skip=skip, limit=limit)
    return users


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user. Users can only update their own profile."""
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only update your own profile")
    
    user = crud_pro.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete user. Users can only delete their own account."""
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only delete your own account")
    
    success = crud_pro.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True}


@router.get("/{user_id}/projects", response_model=list)
async def get_user_projects(
    user_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's projects."""
    current = crud_pro.get_user(db, current_user)
    if current_user != user_id and (not current or current.role != UserRoleEnum.admin):
        raise HTTPException(status_code=403, detail="Access denied")

    projects = crud_pro.get_user_projects(db, user_id)
    return projects
