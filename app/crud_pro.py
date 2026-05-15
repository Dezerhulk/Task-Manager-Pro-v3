"""CRUD operations with audit logging and business logic."""

from datetime import datetime
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import bcrypt

from .models_pro import User, Project, Task, Comment, Tag, AuditLog, RefreshToken, UserRoleEnum
from .schemas_pro import (
    UserCreate, UserUpdate, ProjectCreate, ProjectUpdate, TaskCreate, TaskUpdate,
    CommentCreate, CommentUpdate, TagCreate, TagUpdate, TaskFilterParams, ProjectFilterParams
)

# ===================== Utility Functions =====================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """Authenticate user by username or email."""
    user = get_user_by_username(db, identifier)
    if not user:
        user = get_user_by_email(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_audit_log(
    db: Session,
    user_id: Optional[int],
    entity_type: str,
    action: str,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    comment_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
):
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        project_id=project_id,
        task_id=task_id,
        comment_id=comment_id,
        entity_type=entity_type,
        action=action,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(log)
    db.commit()


# ===================== User CRUD =====================

def create_user(db: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    # Check for existing user
    if db.query(User).filter(User.email == user_create.email).first():
        raise ValueError(f"User with email {user_create.email} already exists")
    if db.query(User).filter(User.username == user_create.username).first():
        raise ValueError(f"User with username {user_create.username} already exists")
    
    db_user = User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        role=user_create.role,
        is_active=user_create.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Audit log
    create_audit_log(
        db, db_user.id, "user", "create",
        new_values={"username": user_create.username, "email": user_create.email, "role": user_create.role.value}
    )
    
    return db_user


def save_refresh_token(db: Session, user_id: int, jti: str, expires_at: datetime) -> RefreshToken:
    """Persist a refresh token record for rotation and revocation."""
    db_refresh_token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
    )
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)
    return db_refresh_token


def get_refresh_token(db: Session, jti: str) -> Optional[RefreshToken]:
    """Get a refresh token record by JTI."""
    return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()


def revoke_refresh_token(db: Session, jti: str) -> bool:
    """Revoke the refresh token record."""
    refresh_token = get_refresh_token(db, jti)
    if not refresh_token or refresh_token.is_revoked:
        return False
    refresh_token.is_revoked = True
    db.commit()
    return True


def revoke_user_refresh_tokens(db: Session, user_id: int) -> int:
    """Revoke all active refresh tokens for a user."""
    tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).all()
    count = 0
    for token in tokens:
        token.is_revoked = True
        count += 1
    db.commit()
    return count


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 20) -> Tuple[List[User], int]:
    """Get paginated list of users."""
    total = db.query(func.count(User.id)).scalar()
    users = db.query(User).offset(skip).limit(limit).all()
    return users, total


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    old_values = {}
    new_values = {}
    
    if user_update.username and user_update.username != db_user.username:
        old_values["username"] = db_user.username
        new_values["username"] = user_update.username
        db_user.username = user_update.username
    
    if user_update.email and user_update.email != db_user.email:
        old_values["email"] = db_user.email
        new_values["email"] = user_update.email
        db_user.email = user_update.email
    
    if user_update.password:
        db_user.password_hash = hash_password(user_update.password)
        new_values["password_changed"] = True
    
    if user_update.role and user_update.role != db_user.role:
        old_values["role"] = db_user.role.value
        new_values["role"] = user_update.role.value
        db_user.role = user_update.role
    
    if user_update.is_active is not None and user_update.is_active != db_user.is_active:
        old_values["is_active"] = db_user.is_active
        new_values["is_active"] = user_update.is_active
        db_user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(db_user)
    
    if old_values:
        create_audit_log(db, user_id, "user", "update", old_values=old_values, new_values=new_values)
    
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Soft delete user."""
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db_user.is_active = False
    db.commit()
    create_audit_log(db, user_id, "user", "delete")
    return True


# ===================== Project CRUD =====================

def create_project(db: Session, project_create: ProjectCreate, owner_id: int) -> Project:
    """Create a new project."""
    db_project = Project(
        title=project_create.title,
        description=project_create.description,
        owner_id=owner_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    create_audit_log(
        db, owner_id, "project", "create", project_id=db_project.id,
        new_values={"title": project_create.title}
    )
    
    return db_project


def get_project(db: Session, project_id: int, include_deleted: bool = False) -> Optional[Project]:
    """Get project by ID."""
    query = db.query(Project).filter(Project.id == project_id)
    if not include_deleted:
        query = query.filter(Project.is_deleted == False)
    return query.first()


def get_projects(db: Session, skip: int = 0, limit: int = 20) -> Tuple[List[Project], int]:
    """Get paginated list of projects."""
    total = db.query(func.count(Project.id)).filter(Project.is_deleted == False).scalar()
    projects = db.query(Project).filter(Project.is_deleted == False).offset(skip).limit(limit).all()
    return projects, total


def get_user_projects(db: Session, user_id: int) -> List[Project]:
    """Get user's projects (owned or member of)."""
    return db.query(Project).filter(
        or_(
            Project.owner_id == user_id,
            Project.members.any(User.id == user_id)
        ),
        Project.is_deleted == False
    ).all()


def search_projects(db: Session, params: ProjectFilterParams) -> Tuple[List[Project], int]:
    """Search/filter projects."""
    query = db.query(Project).filter(Project.is_deleted == False)
    
    if params.owner_id:
        query = query.filter(Project.owner_id == params.owner_id)
    
    if params.member_id:
        query = query.filter(Project.members.any(User.id == params.member_id))
    
    if params.search:
        query = query.filter(Project.title.ilike(f"%{params.search}%"))
    
    total = query.count()
    
    if params.order_by:
        order_col = getattr(Project, params.order_by, None)
        if order_col:
            order_dir = getattr(order_col, params.order_direction)()
            query = query.order_by(order_dir)
    
    projects = query.offset(params.skip).limit(params.limit).all()
    return projects, total


def update_project(db: Session, project_id: int, project_update: ProjectUpdate, user_id: int) -> Optional[Project]:
    """Update project."""
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    old_values = {}
    new_values = {}
    
    if project_update.title and project_update.title != db_project.title:
        old_values["title"] = db_project.title
        new_values["title"] = project_update.title
        db_project.title = project_update.title
    
    if project_update.description is not None and project_update.description != db_project.description:
        old_values["description"] = db_project.description
        new_values["description"] = project_update.description
        db_project.description = project_update.description
    
    db.commit()
    db.refresh(db_project)
    
    if old_values:
        create_audit_log(db, user_id, "project", "update", project_id=project_id, old_values=old_values, new_values=new_values)
    
    return db_project


def delete_project(db: Session, project_id: int, user_id: int) -> bool:
    """Soft delete project."""
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db_project.is_deleted = True
    db_project.deleted_at = datetime.utcnow()
    db.commit()
    create_audit_log(db, user_id, "project", "delete", project_id=project_id)
    return True


def add_project_member(db: Session, project_id: int, user_id: int, actor_id: int) -> bool:
    """Add member to project."""
    db_project = get_project(db, project_id)
    db_user = get_user(db, user_id)
    if not db_project or not db_user:
        return False
    
    if db_user not in db_project.members:
        db_project.members.append(db_user)
        db.commit()
        create_audit_log(db, actor_id, "project", "update", project_id=project_id, new_values={"member_added": user_id})
    
    return True


def remove_project_member(db: Session, project_id: int, user_id: int, actor_id: int) -> bool:
    """Remove member from project."""
    db_project = get_project(db, project_id)
    db_user = get_user(db, user_id)
    if not db_project or not db_user:
        return False
    
    if db_user in db_project.members:
        db_project.members.remove(db_user)
        db.commit()
        create_audit_log(db, actor_id, "project", "update", project_id=project_id, new_values={"member_removed": user_id})
    
    return True


# ===================== Tag CRUD =====================

def create_tag(db: Session, tag_create: TagCreate) -> Tag:
    """Create a new tag."""
    # Check for duplicate
    if db.query(Tag).filter(Tag.name == tag_create.name).first():
        raise ValueError(f"Tag with name '{tag_create.name}' already exists")
    
    db_tag = Tag(name=tag_create.name, color=tag_create.color)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def get_tag(db: Session, tag_id: int) -> Optional[Tag]:
    """Get tag by ID."""
    return db.query(Tag).filter(Tag.id == tag_id).first()


def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
    """Get tag by name."""
    return db.query(Tag).filter(Tag.name == name).first()


def get_tags(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[Tag], int]:
    """Get paginated list of tags."""
    total = db.query(func.count(Tag.id)).scalar()
    tags = db.query(Tag).offset(skip).limit(limit).all()
    return tags, total


def update_tag(db: Session, tag_id: int, tag_update: TagUpdate) -> Optional[Tag]:
    """Update tag."""
    db_tag = get_tag(db, tag_id)
    if not db_tag:
        return None
    
    if tag_update.name and tag_update.name != db_tag.name:
        db_tag.name = tag_update.name
    
    if tag_update.color is not None and tag_update.color != db_tag.color:
        db_tag.color = tag_update.color
    
    db.commit()
    db.refresh(db_tag)
    return db_tag


def delete_tag(db: Session, tag_id: int) -> bool:
    """Delete tag."""
    db_tag = get_tag(db, tag_id)
    if not db_tag:
        return False
    
    db.delete(db_tag)
    db.commit()
    return True


# ===================== Task CRUD =====================

def create_task(db: Session, task_create: TaskCreate, creator_id: int) -> Optional[Task]:
    """Create a new task."""
    # Verify project exists
    project = get_project(db, task_create.project_id)
    if not project:
        return None
    
    db_task = Task(
        project_id=task_create.project_id,
        creator_id=creator_id,
        assignee_id=task_create.assignee_id,
        title=task_create.title,
        description=task_create.description,
        status=task_create.status,
        priority=task_create.priority,
        deadline=task_create.deadline,
    )
    
    # Add tags
    if task_create.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(task_create.tag_ids)).all()
        db_task.tags.extend(tags)
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    create_audit_log(
        db, creator_id, "task", "create", project_id=task_create.project_id, task_id=db_task.id,
        new_values={"title": task_create.title, "status": task_create.status.value}
    )
    
    return db_task


def get_task(db: Session, task_id: int, include_deleted: bool = False) -> Optional[Task]:
    """Get task by ID."""
    query = db.query(Task).filter(Task.id == task_id)
    if not include_deleted:
        query = query.filter(Task.is_deleted == False)
    return query.first()


def get_project_tasks(db: Session, project_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[Task], int]:
    """Get tasks for a project."""
    total = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id,
        Task.is_deleted == False
    ).scalar()
    
    tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.is_deleted == False
    ).offset(skip).limit(limit).all()
    
    return tasks, total


def search_tasks(db: Session, params: TaskFilterParams, current_user_id: Optional[int] = None) -> Tuple[List[Task], int]:
    """Search/filter tasks with advanced filtering."""
    query = db.query(Task).filter(Task.is_deleted == False)

    if current_user_id is not None:
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user or user.role != UserRoleEnum.admin:
            query = query.filter(
                or_(
                    Task.creator_id == current_user_id,
                    Task.assignee_id == current_user_id,
                    Task.project.has(Project.owner_id == current_user_id),
                    Task.project.has(Project.members.any(User.id == current_user_id)),
                )
            )

    if params.project_id:
        query = query.filter(Task.project_id == params.project_id)
    
    if params.assignee_id:
        query = query.filter(Task.assignee_id == params.assignee_id)
    
    if params.creator_id:
        query = query.filter(Task.creator_id == params.creator_id)
    
    if params.status:
        query = query.filter(Task.status == params.status)
    
    if params.priority:
        query = query.filter(Task.priority == params.priority)
    
    if params.tag_ids:
        query = query.filter(Task.tags.any(Tag.id.in_(params.tag_ids)))
    
    if params.search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{params.search}%"),
                Task.description.ilike(f"%{params.search}%")
            )
        )
    
    total = query.count()
    
    if params.order_by:
        order_col = getattr(Task, params.order_by, None)
        if order_col:
            order_dir = getattr(order_col, params.order_direction)()
            query = query.order_by(order_dir)
    
    tasks = query.offset(params.skip).limit(params.limit).all()
    return tasks, total


def update_task(db: Session, task_id: int, task_update: TaskUpdate, user_id: int) -> Optional[Task]:
    """Update task."""
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    old_values = {}
    new_values = {}
    
    if task_update.title and task_update.title != db_task.title:
        old_values["title"] = db_task.title
        new_values["title"] = task_update.title
        db_task.title = task_update.title
    
    if task_update.description is not None and task_update.description != db_task.description:
        old_values["description"] = db_task.description
        new_values["description"] = task_update.description
        db_task.description = task_update.description
    
    if task_update.status and task_update.status != db_task.status:
        old_values["status"] = db_task.status.value
        new_values["status"] = task_update.status.value
        db_task.status = task_update.status
    
    if task_update.priority and task_update.priority != db_task.priority:
        old_values["priority"] = db_task.priority.value
        new_values["priority"] = task_update.priority.value
        db_task.priority = task_update.priority
    
    if task_update.deadline is not None and task_update.deadline != db_task.deadline:
        old_values["deadline"] = db_task.deadline.isoformat() if db_task.deadline else None
        new_values["deadline"] = task_update.deadline.isoformat()
        db_task.deadline = task_update.deadline
    
    if task_update.assignee_id is not None and task_update.assignee_id != db_task.assignee_id:
        old_values["assignee_id"] = db_task.assignee_id
        new_values["assignee_id"] = task_update.assignee_id
        db_task.assignee_id = task_update.assignee_id
    
    if task_update.tag_ids is not None:
        db_task.tags.clear()
        if task_update.tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(task_update.tag_ids)).all()
            db_task.tags.extend(tags)
        new_values["tags"] = task_update.tag_ids
    
    db.commit()
    db.refresh(db_task)
    
    if old_values:
        create_audit_log(db, user_id, "task", "update", task_id=task_id, project_id=db_task.project_id, old_values=old_values, new_values=new_values)
    
    return db_task


def delete_task(db: Session, task_id: int, user_id: int) -> bool:
    """Soft delete task."""
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    
    db_task.is_deleted = True
    db_task.deleted_at = datetime.utcnow()
    db.commit()
    create_audit_log(db, user_id, "task", "delete", task_id=task_id, project_id=db_task.project_id)
    return True


# ===================== Comment CRUD =====================

def create_comment(db: Session, task_id: int, user_id: int, comment_create: CommentCreate) -> Optional[Comment]:
    """Create a new comment."""
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    db_comment = Comment(
        task_id=task_id,
        user_id=user_id,
        content=comment_create.content,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    create_audit_log(
        db, user_id, "comment", "create", task_id=task_id, comment_id=db_comment.id, project_id=db_task.project_id,
        new_values={"content": comment_create.content[:50]}
    )
    
    return db_comment


def get_comment(db: Session, comment_id: int, include_deleted: bool = False) -> Optional[Comment]:
    """Get comment by ID."""
    query = db.query(Comment).filter(Comment.id == comment_id)
    if not include_deleted:
        query = query.filter(Comment.is_deleted == False)
    return query.first()


def get_task_comments(db: Session, task_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[Comment], int]:
    """Get comments for a task."""
    total = db.query(func.count(Comment.id)).filter(
        Comment.task_id == task_id,
        Comment.is_deleted == False
    ).scalar()
    
    comments = db.query(Comment).filter(
        Comment.task_id == task_id,
        Comment.is_deleted == False
    ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    return comments, total


def update_comment(db: Session, comment_id: int, comment_update: CommentUpdate, user_id: int) -> Optional[Comment]:
    """Update comment."""
    db_comment = get_comment(db, comment_id)
    if not db_comment:
        return None
    
    old_content = db_comment.content if comment_update.content else None
    
    if comment_update.content:
        db_comment.content = comment_update.content
    
    db.commit()
    db.refresh(db_comment)
    
    if comment_update.content:
        create_audit_log(db, user_id, "comment", "update", comment_id=comment_id, task_id=db_comment.task_id, old_values={"content": old_content}, new_values={"content": comment_update.content})
    
    return db_comment


def delete_comment(db: Session, comment_id: int, user_id: int) -> bool:
    """Soft delete comment."""
    db_comment = get_comment(db, comment_id)
    if not db_comment:
        return False
    
    db_comment.is_deleted = True
    db_comment.deleted_at = datetime.utcnow()
    db.commit()
    create_audit_log(db, user_id, "comment", "delete", comment_id=comment_id, task_id=db_comment.task_id)
    return True


# ===================== Audit Log CRUD =====================

def get_audit_logs(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[AuditLog], int]:
    """Get audit logs with optional filtering."""
    query = db.query(AuditLog)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if entity_id:
        # Map entity_id to appropriate foreign key
        if entity_type == "user":
            query = query.filter(AuditLog.user_id == entity_id)
        elif entity_type == "project":
            query = query.filter(AuditLog.project_id == entity_id)
        elif entity_type == "task":
            query = query.filter(AuditLog.task_id == entity_id)
        elif entity_type == "comment":
            query = query.filter(AuditLog.comment_id == entity_id)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return logs, total
