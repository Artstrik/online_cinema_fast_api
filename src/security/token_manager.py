from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError, ExpiredSignatureError

from src.exceptions.security import TokenExpiredError, InvalidTokenError
from src.security.interfaces import JWTAuthManagerInterface


class JWTAuthManager(JWTAuthManagerInterface):
    """
    A manager for creating, decoding, and verifying JWT access and refresh tokens.
    """

    _ACCESS_KEY_TIMEDELTA_MINUTES = 60
    _REFRESH_KEY_TIMEDELTA_MINUTES = 60 * 24 * 7

    def __init__(self, secret_key_access: str, secret_key_refresh: str, algorithm: str):
        self._secret_key_access = secret_key_access
        self._secret_key_refresh = secret_key_refresh
        self._algorithm = algorithm

    def _create_token(
        self,
        data: dict,
        secret_key: str,
        expires_delta: timedelta,
        token_type: str,  # "access" | "refresh"
    ) -> str:
        to_encode = data.copy()

        # Unique token ID for revocation support
        if "jti" not in to_encode:
            to_encode["jti"] = uuid.uuid4().hex

        # Token type helps prevent mixing access/refresh
        to_encode["type"] = token_type

        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, secret_key, algorithm=self._algorithm)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        return self._create_token(
            data=data,
            secret_key=self._secret_key_access,
            expires_delta=expires_delta or timedelta(minutes=self._ACCESS_KEY_TIMEDELTA_MINUTES),
            token_type="access",
        )

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        return self._create_token(
            data=data,
            secret_key=self._secret_key_refresh,
            expires_delta=expires_delta or timedelta(minutes=self._REFRESH_KEY_TIMEDELTA_MINUTES),
            token_type="refresh",
        )

    def decode_access_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._secret_key_access, algorithms=[self._algorithm])
            if payload.get("type") != "access":
                raise InvalidTokenError
            return payload
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError

    def decode_refresh_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self._secret_key_refresh, algorithms=[self._algorithm])
            if payload.get("type") != "refresh":
                raise InvalidTokenError
            return payload
        except ExpiredSignatureError:
            raise TokenExpiredError
        except JWTError:
            raise InvalidTokenError

    def verify_refresh_token_or_raise(self, token: str) -> None:
        self.decode_refresh_token(token)

    def verify_access_token_or_raise(self, token: str) -> None:
        self.decode_access_token(token)
