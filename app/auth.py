"""Authentication and authorization utilities."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .config import settings

security = HTTPBearer()


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: int  # user_id
    exp: datetime
    type: str = "access"  # access or refresh


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def hash_password(password: str) -> str:
    """Hash a password."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta is None:
        expires_delta = settings.access_token_expire

    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        payload, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """Create JWT refresh token and return token with JTI."""
    expire = datetime.utcnow() + settings.refresh_token_expire
    jti = str(uuid4())
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": jti,
    }

    encoded_jwt = jwt.encode(
        payload, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt, jti


def verify_refresh_token(token: str) -> Optional[tuple[int, str]]:
    """Verify refresh token and return user_id plus token identifier."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload.get("sub"))
        token_type_claim = payload.get("type", "access")
        if token_type_claim != "refresh":
            return None
        jti = payload.get("jti")
        if not jti:
            return None
        return user_id, jti
    except (JWTError, ValueError):
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[int]:
    """Verify JWT token and return user_id."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = int(payload.get("sub"))
        token_type_claim: str = payload.get("type", "access")

        if token_type_claim != token_type:
            return None

        return user_id
    except (JWTError, ValueError):
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Dependency to get current user from token."""
    token = credentials.credentials

    user_id = verify_token(token, token_type="access")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[int]:
    """Optional dependency to get current user."""
    if credentials is None:
        return None

    user_id = verify_token(credentials.credentials, token_type="access")
    return user_id
