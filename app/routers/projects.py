"""Project management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..auth import get_current_user
from ..models_pro import UserRoleEnum
from ..permissions import check_project_access, PermissionError
from .. import crud_pro
from ..schemas_pro import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    ProjectFilterParams, TaskResponse, AuditLogResponse,
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    project_create: ProjectCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    return crud_pro.create_project(db, project_create, current_user)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project_detail(
    project_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details."""
    await check_project_access(db, project_id, current_user)
    project = crud_pro.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectResponse])
async def get_projects_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of user's projects."""
    projects = crud_pro.get_user_projects(db, current_user)
    return projects[skip : skip + limit]


@router.get("/user/{user_id}/projects", response_model=list[ProjectResponse])
async def get_user_projects(
    user_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific user's projects."""
    current = crud_pro.get_user(db, current_user)
    if current_user != user_id and (not current or current.role != UserRoleEnum.admin):
        raise HTTPException(status_code=403, detail="Access denied")
    projects = crud_pro.get_user_projects(db, user_id)
    return projects


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def get_project_tasks(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tasks for a project."""
    await check_project_access(db, project_id, current_user)
    tasks, _ = crud_pro.get_project_tasks(db, project_id, skip=skip, limit=limit)
    return tasks


@router.get("/{project_id}/audit-logs", response_model=list[AuditLogResponse])
async def get_project_audit_logs(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for a project."""
    await check_project_access(db, project_id, current_user)
    logs, _ = crud_pro.get_audit_logs(db, entity_type="project", entity_id=project_id, skip=skip, limit=limit)
    return logs


@router.post("/search", response_model=list[ProjectResponse])
async def search_projects(
    params: ProjectFilterParams,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search/filter projects."""
    projects, _ = crud_pro.search_projects(db, params)
    return projects


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project."""
    await check_project_access(db, project_id, current_user, require_owner=True)
    project = crud_pro.update_project(db, project_id, project_update, current_user)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete project."""
    await check_project_access(db, project_id, current_user, require_owner=True)
    success = crud_pro.delete_project(db, project_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}


@router.post("/{project_id}/members/{user_id}")
async def add_project_member(
    project_id: int,
    user_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add member to project."""
    await check_project_access(db, project_id, current_user, require_owner=True)
    success = crud_pro.add_project_member(db, project_id, user_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add member")
    return {"added": True}


@router.delete("/{project_id}/members/{user_id}")
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove member from project."""
    await check_project_access(db, project_id, current_user, require_owner=True)
    success = crud_pro.remove_project_member(db, project_id, user_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove member")
    return {"removed": True}

