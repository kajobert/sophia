"""
services/token_service.py
Generování, ověřování a rotace refresh tokenů (JWT).
"""
import os
import time
import jwt
from core import config as sophia_config

JWT_SECRET = sophia_config.SECRET_KEY
JWT_ALG = "HS256"
REFRESH_TOKEN_EXP = 60 * 60 * 24 * 14  # 14 dní


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(time.time()),
        "exp": int(time.time()) + REFRESH_TOKEN_EXP,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def verify_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError("Not a refresh token")
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid refresh token: {str(e)}")
