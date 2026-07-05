"""
SBI Vishwas — Auth Middleware

FastAPI dependencies for authentication and authorization.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import TokenPayload, jwt_manager
from src.auth.rbac import check_any_permission, check_permission
from src.database.engine import get_session


security_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Authenticated user context available in routes."""
    id: uuid.UUID
    email: str | None = None
    full_name: str | None = None
    roles: list[str] = []
    permissions: list[str] = []
    branch_code: str | None = None
    is_superuser: bool = False


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)] = None,
) -> CurrentUser:
    """
    FastAPI dependency: extract and validate the current user from JWT.

    Raises 401 if no token or token is invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_manager.verify_token_type(credentials.credentials, "access")
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        id=uuid.UUID(payload.sub),
        roles=payload.roles,
        permissions=payload.permissions,
        branch_code=payload.branch_code,
        is_superuser="superadmin" in payload.roles,
    )


async def get_current_active_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Dependency: ensure the current user is active (not disabled/locked)."""
    # In production, this would check the DB for is_active/locked_until
    # For now, if the token is valid, the user is considered active
    return current_user


class PermissionChecker:
    """
    Dependency factory for checking permissions.

    Usage:
        @router.get("/...", dependencies=[Depends(PermissionChecker("customer:read"))])
        async def endpoint(...):
            ...
    """

    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    async def __call__(
        self,
        current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    ) -> CurrentUser:
        if current_user.is_superuser:
            return current_user

        if not check_permission(current_user.permissions, self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {self.required_permission}",
            )

        return current_user


class AnyPermissionChecker:
    """
    Dependency factory: user must have at least one of the listed permissions.
    """

    def __init__(self, *required_permissions: str) -> None:
        self.required_permissions = list(required_permissions)

    async def __call__(
        self,
        current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    ) -> CurrentUser:
        if current_user.is_superuser:
            return current_user

        if not check_any_permission(current_user.permissions, self.required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {self.required_permissions}",
            )

        return current_user


class BranchScopeChecker:
    """
    Dependency factory: enforce branch-scoped access.

    Users can only access data from their assigned branch unless
    they have a cross-branch permission or are superadmin.
    """

    def __init__(self, cross_branch_permission: str = "admin:full") -> None:
        self.cross_branch_permission = cross_branch_permission

    async def __call__(
        self,
        request: Request,
        current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    ) -> CurrentUser:
        if current_user.is_superuser:
            return current_user

        if check_permission(current_user.permissions, self.cross_branch_permission):
            return current_user

        # Check if the request targets a specific branch
        branch_code = request.query_params.get("branch_code") or request.path_params.get("branch_code")

        if branch_code and branch_code != current_user.branch_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: you can only access data from branch {current_user.branch_code}",
            )

        return current_user
