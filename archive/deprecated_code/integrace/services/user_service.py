"""
services/user_service.py
Logika pro správu uživatelů a session.
"""

from fastapi import Request, HTTPException


def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def set_user_session(request: Request, user: dict):
    request.session["user"] = user


def clear_user_session(request: Request):
    request.session.pop("user", None)
