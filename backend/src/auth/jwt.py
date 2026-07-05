"""
SBI Vishwas — JWT Authentication

JWT token creation, validation, and refresh with configurable algorithms and expiry.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pydantic import BaseModel

from src.config.settings import get_settings


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str  # user ID
    exp: datetime
    iat: datetime
    iss: str
    jti: str  # unique token ID
    type: str  # access or refresh
    roles: list[str] = []
    permissions: list[str] = []
    branch_code: str | None = None


class TokenPair(BaseModel):
    """Access + refresh token pair returned after login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class JWTManager:
    """
    JWT token management with support for access/refresh token flow.

    - Access tokens are short-lived (configurable, default 30 min).
    - Refresh tokens are longer-lived (configurable, default 7 days).
    - Each token has a unique JTI for revocation support.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def create_access_token(
        self,
        user_id: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        branch_code: str | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a short-lived access token."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.settings.jwt_access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "iss": self.settings.jwt_issuer,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "roles": roles or [],
            "permissions": permissions or [],
            "branch_code": branch_code,
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        """
        Create a long-lived refresh token.
        Returns (token_string, token_hash) — the hash is stored in DB.
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.settings.jwt_refresh_token_expire_days)
        jti = str(uuid.uuid4())

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "iss": self.settings.jwt_issuer,
            "jti": jti,
            "type": "refresh",
        }

        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

        return token, jti

    def create_token_pair(
        self,
        user_id: str,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        branch_code: str | None = None,
    ) -> tuple[TokenPair, str]:
        """
        Create both access and refresh tokens.
        Returns (TokenPair, refresh_jti) — refresh_jti is stored in DB.
        """
        access_token = self.create_access_token(
            user_id=user_id,
            roles=roles,
            permissions=permissions,
            branch_code=branch_code,
        )

        refresh_token, refresh_jti = self.create_refresh_token(user_id)

        pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.jwt_access_token_expire_minutes * 60,
        )

        return pair, refresh_jti

    def decode_token(self, token: str) -> TokenPayload:
        """
        Decode and validate a JWT token.

        Raises:
            JWTError: If the token is invalid, expired, or tampered with.
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
                issuer=self.settings.jwt_issuer,
            )
            return TokenPayload(**payload)
        except JWTError:
            raise

    def verify_token_type(self, token: str, expected_type: str) -> TokenPayload:
        """Decode and verify the token is of the expected type (access/refresh)."""
        payload = self.decode_token(token)
        if payload.type != expected_type:
            raise JWTError(f"Expected {expected_type} token, got {payload.type}")
        return payload


# Module-level instance
jwt_manager = JWTManager()
