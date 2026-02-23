from collections.abc import Callable
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import get_jwt_auth_manager
from src.database import get_db
from src.database.models.accounts import UserModel, UserGroupEnum
from src.exceptions.security import BaseSecurityError
from src.security.interfaces import JWTAuthManagerInterface


def get_token(request: Request) -> str:
    """
    Extracts the Bearer token from the Authorization header.

    :param request: FastAPI Request object.
    :return: Extracted token string.
    :raises HTTPException: If Authorization header is missing or invalid.
    """
    authorization: str = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'"
        )

    return token


async def get_current_active_user(
        token: str = Depends(get_token),
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        db: AsyncSession = Depends(get_db),
) -> UserModel:
    """
    Get current authenticated and active user from JWT token.

    Args:
        token: JWT access token from Authorization header
        jwt_manager: JWT authentication manager
        db: Database session

    Returns:
        UserModel: Authenticated and active user

    Raises:
        HTTPException:
            - 401 if token is invalid or expired
            - 401 if user not found
            - 403 if user is not active
    """
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )

    return user

async def get_current_active_user_optional(
        request: Request,
        jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
        db: AsyncSession = Depends(get_db),
) -> UserModel | None:
    """
    Return current active user when Authorization header is present.

    Allows public endpoints to work for anonymous users, while still returning
    user-specific flags when a valid token is supplied.
    """
    authorization: str | None = request.headers.get("Authorization")
    if not authorization:
        return None

    token = get_token(request)
    try:
        payload = jwt_manager.decode_access_token(token)
        user_id = payload.get("user_id")
    except BaseSecurityError:
        return None

    if user_id is None:
        return None

    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not user.is_active:
        return None

    return user


def require_roles(*roles: UserGroupEnum) -> Callable[[UserModel], UserModel]:
    """Dependency factory to enforce role-based access control."""

    async def role_checker(current_user: UserModel = Depends(get_current_active_user)) -> UserModel:
        if current_user.group.name not in roles:
            allowed = ", ".join(role.value for role in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed}."
            )
        return current_user

    return role_checker
