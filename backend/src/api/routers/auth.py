"""
SBI Vishwas — Authentication Router

Login, register, refresh, logout endpoints with password hashing and JWT.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import TokenPair, jwt_manager
from src.auth.middleware import CurrentUser, get_current_active_user
from src.auth.rbac import ROLE_PERMISSIONS, SystemRole
from src.database.engine import get_session
from src.database.models.user import RefreshToken, Role, User, UserRole

logger = structlog.get_logger(__name__)

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Schemas
# =============================================================================


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    employee_id: str | None = None
    branch_code: str | None = None
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    employee_id: str | None
    branch_code: str | None
    roles: list[str]
    is_active: bool

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    """Register a new system user with default viewer role."""

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash password
    hashed_password = pwd_context.hash(request.password)

    # Create user
    user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=hashed_password,
        employee_id=request.employee_id,
        branch_code=request.branch_code,
        phone=request.phone,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Assign default role (viewer)
    viewer_role = await db.execute(
        select(Role).where(Role.name == SystemRole.VIEWER.value)
    )
    role = viewer_role.scalar_one_or_none()
    if role:
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)

    await db.flush()

    # Generate tokens
    roles = [SystemRole.VIEWER.value]
    permissions = ROLE_PERMISSIONS.get(SystemRole.VIEWER.value, [])

    token_pair, refresh_jti = jwt_manager.create_token_pair(
        user_id=str(user.id),
        roles=roles,
        permissions=permissions,
        branch_code=user.branch_code,
    )

    # Store refresh token
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=refresh_jti,
        expires_at=datetime.now(timezone.utc).__add__(
            __import__("datetime").timedelta(days=7)
        ),
    )
    db.add(refresh_token_record)

    logger.info("User registered", user_id=str(user.id), email=user.email)

    return AuthResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            employee_id=user.employee_id,
            branch_code=user.branch_code,
            roles=roles,
            is_active=user.is_active,
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    """Authenticate user and return JWT tokens."""

    # Find user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    # Get user roles and permissions
    role_result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    roles_list = role_result.scalars().all()
    role_names = [r.name for r in roles_list]
    permissions: list[str] = []
    for r in roles_list:
        permissions.extend(r.permissions)
    permissions = list(set(permissions))

    # Generate tokens
    token_pair, refresh_jti = jwt_manager.create_token_pair(
        user_id=str(user.id),
        roles=role_names,
        permissions=permissions,
        branch_code=user.branch_code,
    )

    # Store refresh token
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=refresh_jti,
        expires_at=datetime.now(timezone.utc).__add__(
            __import__("datetime").timedelta(days=7)
        ),
        ip_address=http_request.client.host if http_request.client else None,
        device_info=http_request.headers.get("User-Agent", "")[:500],
    )
    db.add(refresh_token_record)

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    user.failed_login_attempts = 0

    logger.info("User logged in", user_id=str(user.id))

    return AuthResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            employee_id=user.employee_id,
            branch_code=user.branch_code,
            roles=role_names,
            is_active=user.is_active,
        ),
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh access token",
)
async def refresh_token(
    request: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TokenPair:
    """Use a refresh token to get a new access token."""
    from jose import JWTError

    try:
        payload = jwt_manager.verify_token_type(request.refresh_token, "refresh")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify refresh token exists and is not revoked
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == payload.jti,
            RefreshToken.is_revoked == False,
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Get user with roles
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(payload.sub)))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    role_result = await db.execute(
        select(Role).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
    )
    roles_list = role_result.scalars().all()
    role_names = [r.name for r in roles_list]
    permissions = list({p for r in roles_list for p in r.permissions})

    # Revoke old refresh token
    stored_token.is_revoked = True

    # Create new token pair
    token_pair, new_refresh_jti = jwt_manager.create_token_pair(
        user_id=str(user.id),
        roles=role_names,
        permissions=permissions,
        branch_code=user.branch_code,
    )

    # Store new refresh token
    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=new_refresh_jti,
        expires_at=datetime.now(timezone.utc).__add__(
            __import__("datetime").timedelta(days=7)
        ),
    )
    db.add(new_refresh)

    return token_pair


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — revoke refresh token",
)
async def logout(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Revoke all refresh tokens for the current user."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False,
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.is_revoked = True

    logger.info("User logged out", user_id=str(current_user.id))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """Get the currently authenticated user's profile."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        employee_id=user.employee_id,
        branch_code=user.branch_code,
        roles=current_user.roles,
        is_active=user.is_active,
    )
