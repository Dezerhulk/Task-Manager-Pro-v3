"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# Authentication schemas
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8, max_length=100)

    model_config = {"extra": "forbid"}

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=100)

    model_config = {"extra": "forbid"}


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = {"extra": "forbid"}


# Enums
class UserRoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class TaskStatusEnum(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"
    archived = "archived"


class TaskPriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    role: UserRoleEnum = UserRoleEnum.user
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserDetailResponse(UserResponse):
    created_tasks: List["TaskResponse"] = []
    assigned_tasks: List["TaskResponse"] = []
    projects: List["ProjectResponse"] = []
    comments: List["CommentResponse"] = []


# Project schemas
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    owner: UserResponse
    members: List[UserResponse] = []
    tasks: List["TaskResponse"] = []


# Tag schemas
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    id: int
    name: str
    color: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# Task schemas
class TaskCreate(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.todo
    priority: TaskPriorityEnum = TaskPriorityEnum.medium
    deadline: Optional[datetime] = None
    assignee_id: Optional[int] = None
    tag_ids: List[int] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    deadline: Optional[datetime] = None
    assignee_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    deadline: Optional[datetime]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskDetailResponse(TaskResponse):
    creator_id: Optional[int]
    assignee_id: Optional[int]
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    comments: List["CommentResponse"] = []
    tags: List[TagResponse] = []


# Comment schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentDetailResponse(CommentResponse):
    user: UserResponse


# Search/Filter schemas
class TaskFilterParams(BaseModel):
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    creator_id: Optional[int] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    tag_ids: List[int] = []
    search: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
    order_by: Optional[str] = None
    order_direction: str = Field("asc", pattern="^(asc|desc)$")


class ProjectFilterParams(BaseModel):
    search: Optional[str] = None
    owner_id: Optional[int] = None
    member_id: Optional[int] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
    order_by: Optional[str] = None
    order_direction: str = Field("asc", pattern="^(asc|desc)$")


# Audit Log schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    project_id: Optional[int]
    task_id: Optional[int]
    comment_id: Optional[int]
    entity_type: str
    action: str
    old_values: Optional[dict]
    new_values: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


# Update forward references
TaskDetailResponse.model_rebuild()
TaskResponse.model_rebuild()
UserDetailResponse.model_rebuild()
ProjectDetailResponse.model_rebuild()
CommentDetailResponse.model_rebuild()
