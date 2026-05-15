# Task Manager Pro v3.0

A FastAPI task management API with JWT authentication, SQLAlchemy persistence, role-based authorization, refresh token rotation, and production-safe configuration.

## 🎯 Features

- ✅ **JWT Authentication**: Secure access tokens + refresh tokens
- ✅ **User Management**: Role-based access control (Admin, Manager, User)  
- ✅ **Project Management**: Create projects with team members
- ✅ **Task Management**: Full lifecycle with priorities, deadlines, soft delete
- ✅ **Comments**: Threaded discussions on tasks
- ✅ **Tags**: Many-to-many task categorization
- ✅ **Audit Logs**: Complete change tracking with user context
- ✅ **Advanced Search**: Multi-criteria filtering with pagination
- ✅ **Object-Level Auth**: Verify access to specific resources
- ✅ **RBAC**: Role-based access control with permission checks
- ✅ **Error Handling**: Comprehensive database error handling
- ✅ **CORS**: Configurable for production safety
- ✅ **Docker**: Production-ready containerization
- ✅ **Tests**: Pytest suite with coverage reporting
- ✅ **CI/CD**: GitHub Actions pipeline

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.115.0
- **Auth**: JWT with passlib + python-jose
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0+ (SQLite for dev)
- **Config**: Pydantic Settings
- **Migrations**: Alembic 1.12.0
- **Testing**: Pytest 7.4+ with async support
- **Linting**: Ruff, Black, Flake8, MyPy
- **CI/CD**: GitHub Actions
- **Containers**: Docker & Docker Compose

## 📁 Project Structure

```
task_manager_pro/
├── app/
│   ├── __init__.py
│   ├── main_pro.py         # FastAPI app with routes
│   ├── config.py           # Pydantic settings (NEW)
│   ├── auth.py             # JWT utilities (NEW)
│   ├── permissions.py      # RBAC & object-level auth (NEW)
│   ├── models_pro.py       # SQLAlchemy ORM models
│   ├── database_pro.py     # Database setup
│   ├── schemas_pro.py      # Pydantic request/response schemas
│   ├── crud_pro.py         # CRUD operations
│   └── api/                # API routers (organized)
│
├── routers/
│   ├── auth.py            # Authentication endpoints (NEW)
│   ├── users.py           # User endpoints
│   ├── projects.py        # Project endpoints
│   └── tasks.py           # Task endpoints
│
├── tests/
│   ├── test_auth.py       # Auth tests (NEW)
│   ├── test_crud_pro.py   # CRUD tests
│   └── test_api_pro.py    # API tests
│
├── .github/workflows/
│   └── ci.yml             # GitHub Actions CI/CD (NEW)
│
├── pyproject.toml         # Project config with linting (NEW)
├── .pre-commit-config.yaml # Pre-commit hooks (NEW)
├── docker-compose.yml     # Docker Compose config
├── Dockerfile             # Container image
├── requirements.txt       # Dependencies (updated)
├── .env.example          # Environment template (updated)
└── README.md             # This file
```

## 🔐 Security Features

### Authentication (NEW)
- JWT access tokens (30 min default)
- JWT refresh tokens (7 days default)
- Password hashing with bcrypt
- Login/Register endpoints
- Token refresh endpoint

### Authorization (NEW)
- Role-Based Access Control (RBAC)
- Object-level authorization checks
- User ownership verification
- Project membership validation
- Task assignment & creator checks

### Production Security
- Configurable CORS (not open to "*")
- Environment-based secrets
- Password validation
- SQL injection prevention
- Error message sanitization

## 🚀 Quick Start

### 1. Installation

```bash
cd "task manager pro"
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env with your settings (SECRET_KEY must be changed!)
```

### 3. Run Development Server

```bash
uvicorn app.main_pro:app --reload --port 8000
```

Visit API docs: http://localhost:8000/docs

### 4. Run Tests

```bash
pytest tests/ -v --cov=app
```

### 5. Docker Deployment

```bash
docker-compose up -d
docker-compose logs -f app
```

## 🔑 Authentication Flow

### 1. Register
```bash
POST /api/auth/register
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

### 2. Login
```bash
POST /api/auth/login
{
  "email": "john@example.com",
  "password": "securepassword123"
}
Response: {
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Use Token
```bash
GET /api/auth/me
Headers: Authorization: Bearer eyJ...
```

### 4. Refresh Token
```bash
POST /api/auth/refresh
{
  "refresh_token": "eyJ..."
}
Response: {
  "access_token": "new_eyJ...",
  "refresh_token": "new_eyJ...",
  "token_type": "bearer"
}
```

## 📚 API Endpoints

### Authentication
```
POST   /api/auth/register         # Register new user
POST   /api/auth/login            # Login (returns tokens)
POST   /api/auth/refresh          # Refresh access token
POST   /api/auth/logout           # Logout (client discards token)
```

### Users
```
POST   /api/users                # Create user (admin only)
GET    /api/auth/me               # Get current authenticated user profile
GET    /api/users/{id}            # Get user details (self or admin)
PUT    /api/users/{id}            # Update user (self)
DELETE /api/users/{id}            # Delete user (self)
```

### Projects
```
POST   /api/projects              # Create project
GET    /api/projects              # List user's projects
GET    /api/projects/{id}         # Get project details
PUT    /api/projects/{id}         # Update project (owner only)
DELETE /api/projects/{id}         # Delete project (owner only)
POST   /api/projects/{id}/members/{uid}    # Add member (owner only)
DELETE /api/projects/{id}/members/{uid}   # Remove member (owner only)
POST   /api/projects/search       # Search projects
```

### Tasks
```
POST   /api/tasks                 # Create task
GET    /api/tasks/{id}            # Get task details
PUT    /api/tasks/{id}            # Update task (creator/assignee/admin)
DELETE /api/tasks/{id}            # Delete task (creator/admin)
GET    /api/projects/{id}/tasks   # List project tasks
POST   /api/tasks/search          # Search tasks
```

### Comments
```
POST   /api/tasks/{id}/comments       # Add comment
GET    /api/tasks/{id}/comments       # List task comments
PUT    /api/comments/{id}             # Edit comment (author only)
DELETE /api/comments/{id}             # Delete comment (author/admin)
```

## 🔒 Authorization Examples

```python
# Automatic via dependency injection
async def my_endpoint(
    current_user_id: int = Depends(get_current_user),  # Requires login
    db: Session = Depends(get_db)
):
    # current_user_id is now verified
    user = await check_user_exists(db, current_user_id)
    
    # Check project access
    project = await check_project_access(
        db, project_id, current_user_id
    )
    
    # Check role
    await require_role(user, UserRoleEnum.manager)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_login_success -v

# Watch mode (with pytest-watch)
ptw tests/
```

## 💾 Configuration

All config via `.env` file:

```ini
# Database
DATABASE_URL=sqlite:///./task_manager.db  # or postgresql://...

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Security (⚠️  CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (restrict in production)
CORS_ORIGINS=["http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
```

## 🔄 Database Migrations (Alembic)

```bash
# Create migration
alembic revision --autogenerate -m "Add user role"

# Apply migrations
alembic upgrade head

# Revert to previous
alembic downgrade -1

# View migration history
alembic history
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
# Verify DATABASE_URL in .env
# Test connection: psql postgresql://user:pass@localhost:5432/db
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### JWT Token Errors
```bash
# Token expired: Use refresh_token endpoint
# Invalid token: Check SECRET_KEY matches
# Invalid signature: Ensure token not tampered
```

### Tests Failing
```bash
pytest tests/ -vv -s  # Verbose with print statements
pytest tests/test_auth.py -v  # Run specific test file
```

## 📈 Performance Optimization

1. **Pagination**: Use `skip` and `limit` parameters
2. **Indexes**: Database queries use indexes for common filters
3. **Connection Pooling**: SQLAlchemy handles it (default 10 connections)
4. **Caching**: Add Redis for session/token caching if needed
5. **SQL Monitoring**: Set `SQL_ECHO=True` in dev to debug

## 🚀 Production Deployment

### Pre-Deployment Checklist
- [ ] Change `SECRET_KEY` to random secure value (`openssl rand -hex 32`)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure `CORS_ORIGINS` to specific domains
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS
- [ ] Set up proper logging & monitoring
- [ ] Run security checks: `bandit -r app`
- [ ] Run tests: `pytest tests/ --cov`
- [ ] Review `.env` variables

### Docker Deployment
```bash
# Build image
docker build -t task-manager-pro:latest .

# Run with docker-compose
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f app
```

### Manual Deployment
```bash
# With PostgreSQL
createdb task_manager_db

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server with Gunicorn
gunicorn app.main_pro:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## 📊 Project Statistics

- **Models**: 7 (User, Project, Task, Comment, Tag, AuditLog, ProjectMember)
- **API Endpoints**: 25+
- **Test Coverage**: > 80% target
- **Type Coverage**: > 90% with MyPy
- **Dependencies**: 20 core + 10 dev

## 🔗 Useful Links

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc7519)
- [OWASP Security](https://owasp.org/www-project-top-ten/)

## 📝 Development Workflow

```bash
# 1. Create branch
git checkout -b feature/my-feature

# 2. Make changes & commit
git add .
pre-commit run --all-files  # Lint before commit
git commit -m "feat: add my feature"

# 3. Run tests
pytest tests/ -v

# 4. Push & create PR
git push origin feature/my-feature

# 5. GitHub Actions runs automatically
# - Linting (ruff, black, mypy)
# - Tests (pytest with coverage)
# - Security (bandit, safety)
```

## 🎓 Learning Resources

- **Auth**: Check `app/auth.py` and `routers/auth.py`
- **Permissions**: Check `app/permissions.py`
- **Models**: Check `app/models_pro.py`
- **Config**: Check `app/config.py`
- **Tests**: Check `tests/test_auth.py`

## 📄 License

MIT License - See LICENSE file

---

**Built with ❤️ using FastAPI + SQLAlchemy + JWT + PostgreSQL**

**v2.0 Release Notes**:
- ✨ JWT authentication with refresh tokens
- 🔐 Role-based access control (RBAC)
- 🛡️ Object-level authorization checks
- ⚙️ Pydantic Settings for configuration
- 🧪 Pytest test suite with async support
- 🔄 GitHub Actions CI/CD pipeline
- 📝 Pre-commit hooks (ruff, black, mypy)
- 📊 Code coverage reporting
- 🚀 Production-ready security hardening

## 🎯 Features

- ✅ **User Management**: Role-based access control (Admin, Manager, User)
- ✅ **Project Management**: Create projects with team members
- ✅ **Task Management**: Full lifecycle management with priorities and deadlines
- ✅ **Comments**: Discussion threads on tasks
- ✅ **Tags**: Many-to-many task categorization
- ✅ **Soft Delete**: Safe deletion with recovery capability
- ✅ **Audit Logs**: Complete change tracking for compliance
- ✅ **Advanced Search**: Multi-criteria task filtering
- ✅ **Pagination**: Efficient data loading
- ✅ **Transactions**: ACID compliance
- ✅ **Indexes**: Query performance optimization
- ✅ **Docker Support**: Easy containerized deployment

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0+
- **Migrations**: Alembic 1.12.0
- **Security**: Passlib + Bcrypt
- **Validation**: Pydantic 2.5+
- **Testing**: Pytest 7.4+
- **Containers**: Docker & Docker Compose

## 📁 Project Structure

```
task_manager_pro/
├── app/
│   ├── __init__.py
│   ├── models_pro.py       # SQLAlchemy ORM models
│   ├── database_pro.py     # Database configuration
│   ├── schemas_pro.py      # Pydantic schemas
│   ├── crud_pro.py         # CRUD operations
│   └── main_pro.py         # FastAPI app
│
├── tests/
│   ├── conftest_pro.py     # Pytest fixtures
│   ├── test_crud_pro.py    # CRUD tests
│   └── test_api_pro.py     # API tests
│
├── docker-compose.yml      # Docker Compose config
├── Dockerfile              # Container image
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🗄️ Database Schema

**8 Core Tables:**
- `users` - User accounts with roles
- `projects` - Projects with owner/members
- `tasks` - Tasks with status, priority, deadline
- `comments` - Task discussions
- `tags` - Task categories
- `project_members` - User↔Project association
- `task_tags` - Task↔Tag association
- `audit_logs` - Change history

**Key Indexes:**
- Task search: `(project_id, status)`, `(assignee_id, status)`
- Priority/deadline: `(priority, deadline)`
- User lookup: `(email, is_active)`

## 🚀 Quick Start

### 1. Installation

```bash
cd task manager pro
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Development Server

```bash
uvicorn app.main_pro:app --reload --port 8000
```

Visit: http://localhost:8000/docs (Swagger UI)

### 4. Docker Deployment

```bash
docker-compose up -d
docker-compose logs -f app
```

## 📚 API Endpoints

### Users
```
POST   /api/users
GET    /api/users
GET    /api/users/{id}
PUT    /api/users/{id}
DELETE /api/users/{id}
```

### Projects
```
POST   /api/projects
GET    /api/projects
GET    /api/projects/{id}
PUT    /api/projects/{id}
DELETE /api/projects/{id}
POST   /api/projects/{id}/members/{uid}
DELETE /api/projects/{id}/members/{uid}
POST   /api/projects/search
```

### Tasks
```
POST   /api/tasks
GET    /api/tasks/{id}
GET    /api/projects/{id}/tasks
PUT    /api/tasks/{id}
DELETE /api/tasks/{id}
POST   /api/tasks/search
```

### Comments
```
POST   /api/tasks/{id}/comments
GET    /api/tasks/{id}/comments
GET    /api/comments/{id}
PUT    /api/comments/{id}
DELETE /api/comments/{id}
```

### Tags
```
POST   /api/tags
GET    /api/tags
GET    /api/tags/{id}
PUT    /api/tags/{id}
DELETE /api/tags/{id}
```

### Audit Logs
```
GET    /api/audit-logs
GET    /api/tasks/{id}/audit-logs
GET    /api/projects/{id}/audit-logs
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test class
pytest tests/test_crud_pro.py::TestUserCRUD -v
```

## 🔑 Key Models

### Enums
- `UserRole`: admin, manager, user
- `TaskStatus`: todo, in_progress, review, done, archived
- `TaskPriority`: low, medium, high, critical

### CRUD Functions

**Users**
```python
create_user(db, user_create) -> User
get_user(db, user_id) -> Optional[User]
update_user(db, user_id, update_data) -> Optional[User]
delete_user(db, user_id) -> bool
```

**Projects**
```python
create_project(db, project_create, owner_id) -> Project
search_projects(db, params) -> Tuple[List[Project], int]
add_project_member(db, project_id, user_id, actor_id) -> bool
```

**Tasks**
```python
create_task(db, task_create, creator_id) -> Task
search_tasks(db, params) -> Tuple[List[Task], int]
update_task(db, task_id, update_data, user_id) -> Optional[Task]
```

**Comments**
```python
create_comment(db, task_id, user_id, comment_create) -> Optional[Comment]
get_task_comments(db, task_id) -> Tuple[List[Comment], int]
```

**Audit**
```python
get_audit_logs(db, entity_type, entity_id) -> Tuple[List[AuditLog], int]
```

## 🔍 Advanced Features

### Task Search/Filter

```python
TaskFilterParams(
    project_id=1,
    assignee_id=5,
    status="in_progress",
    priority="high",
    tag_ids=[1, 2, 3],
    search="bug",
    skip=0,
    limit=20,
    order_by="deadline",
    order_direction="asc"
)
```

### Soft Delete

All entities support soft deletion:
```python
task.is_deleted = True
task.deleted_at = datetime.utcnow()
db.commit()
```

### Audit Logging

Every change is tracked:
```python
create_audit_log(
    db, user_id, "task", "update",
    old_values={"status": "todo"},
    new_values={"status": "in_progress"}
)
```

## 🐘 PostgreSQL Features

- Connection pooling (10 connections + 20 overflow)
- Foreign key constraints with CASCADE delete
- JSON columns for audit log values
- UTC timezone-aware timestamps
- Query performance indexes

## 🔐 Security

- ✅ Password hashing (bcrypt)
- ✅ SQL injection prevention (parameterized queries)
- ✅ Role-based access ready
- ✅ Audit trail for compliance
- ✅ CORS enabled (configure for production)

## 📋 Environment Variables

```
DATABASE_URL=postgresql://user:pass@host:5432/db
SQL_ECHO=False                  # Log SQL
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
SECRET_KEY=your-secret-key
```

## 🐛 Troubleshooting

**Database connection issues:**
```bash
# Check PostgreSQL is running
# Verify DATABASE_URL is correct
# Check credentials and permissions
```

**Import errors:**
```bash
# Install dependencies
pip install -r requirements.txt

# Add to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

**Tests failing:**
```bash
# Verbose output
pytest tests/ -vv -s

# Check fixtures
pytest tests/conftest_pro.py -v
```

## 📈 Performance Tips

1. Use pagination for large datasets
2. Filter early in search queries
3. Monitor with `SQL_ECHO=True`
4. Use appropriate indexes
5. Consider caching for read-heavy endpoints

## 🚀 Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Manual PostgreSQL

```bash
# Create database
createdb task_manager_db

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main_pro:app --host 0.0.0.0 --port 8000
```

## 📝 Example Usage

```python
from app import crud_pro
from app.schemas_pro import ProjectCreate, TaskCreate

# Create project
project = crud_pro.create_project(
    db,
    ProjectCreate(title="Website Redesign"),
    owner_id=1
)

# Create task
task = crud_pro.create_task(
    db,
    TaskCreate(
        title="Design Homepage",
        project_id=project.id,
        status="todo",
        priority="high"
    ),
    creator_id=1
)

# Search tasks
tasks, total = crud_pro.search_tasks(
    db,
    TaskFilterParams(
        project_id=project.id,
        priority="high",
        limit=10
    )
)
```

## 📞 Support

- Check `/docs` endpoint for interactive API documentation
- Review test examples for usage patterns
- Check audit logs for debugging
- Examine models for schema details

## 📄 License

MIT License

---

**Built with ❤️ using FastAPI + SQLAlchemy + PostgreSQL**
