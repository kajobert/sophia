"""
services/audit_service.py
Logování bezpečnostních akcí a auditních záznamů do souboru.
"""
import os
import datetime
import json
from core import config as sophia_config

LOG_PATH = os.path.join(sophia_config.LOG_DIR, "audit.log")

def log_event(event_type: str, user: dict = None, detail: str = ""):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "user": user.get("email") if user else None,
        "detail": detail,
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
