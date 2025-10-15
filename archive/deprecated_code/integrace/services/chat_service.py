"""
services/chat_service.py
Logika pro zpracování zpráv chatu.
"""


def generate_reply(message: str, user: dict = None) -> str:
    if user:
        username = user.get("name") or user.get("email") or "uživatel"
        return f"Sophia říká {username}: {message}"
    else:
        return f"Sophia říká: {message}"
