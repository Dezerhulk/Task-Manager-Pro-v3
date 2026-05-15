"""Task management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..auth import get_current_user
from ..permissions import check_project_access, check_task_access
from .. import crud_pro
from ..schemas_pro import (
    TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse,
    TaskFilterParams, AuditLogResponse,
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse)
async def create_task(
    task_create: TaskCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new task."""
    await check_project_access(db, task_create.project_id, current_user)
    task = crud_pro.create_task(db, task_create, current_user)
    if not task:
        raise HTTPException(status_code=400, detail="Failed to create task")
    return task


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task_detail(
    task_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get task details."""
    await check_task_access(db, task_id, current_user)
    task = crud_pro.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update task."""
    await check_task_access(db, task_id, current_user)
    task = crud_pro.update_task(db, task_id, task_update, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete task."""
    await check_task_access(db, task_id, current_user)
    success = crud_pro.delete_task(db, task_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}


@router.post("/search", response_model=list[TaskResponse])
async def search_tasks(
    params: TaskFilterParams,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search/filter tasks."""
    if params.project_id:
        await check_project_access(db, params.project_id, current_user)

    tasks, _ = crud_pro.search_tasks(db, params, current_user)
    return tasks


@router.get("/{task_id}/audit-logs", response_model=list[AuditLogResponse])
async def get_task_audit_logs(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit logs for a task."""
    await check_task_access(db, task_id, current_user)
    logs, _ = crud_pro.get_audit_logs(db, entity_type="task", entity_id=task_id, skip=skip, limit=limit)
    return logs

