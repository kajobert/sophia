"""
services/roles.py
Dekorátory a pomocné funkce pro kontrolu rolí a ochranu endpointů.
"""

from fastapi import Request, HTTPException
from functools import wraps
from core import config as sophia_config

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_GUEST = "guest"


def get_user_role(user: dict) -> str:
    if not user:
        return ROLE_GUEST
    email = user.get("email", "")
    if email in sophia_config.ADMIN_EMAILS:
        return ROLE_ADMIN
    return ROLE_USER


def require_role(required_role: str):
    def decorator(endpoint_func):
        @wraps(endpoint_func)
        async def wrapper(request: Request, *args, **kwargs):
            user = request.session.get("user")
            role = get_user_role(user)
            if required_role == ROLE_ADMIN and role != ROLE_ADMIN:
                raise HTTPException(status_code=403, detail="Admin access required")
            if required_role == ROLE_USER and role not in (ROLE_USER, ROLE_ADMIN):
                raise HTTPException(status_code=401, detail="User login required")
            return await endpoint_func(request, *args, **kwargs)

        return wrapper

    return decorator
