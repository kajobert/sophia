from celery import Celery
import os

from core.llm_config import llm
from services.llm_cache import get_cached_reply, set_cached_reply

# Redis URL z prostředí nebo fallback
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("sophia_llm", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(name="llm.generate_reply")
def generate_llm_reply(prompt, user=None):
    # Nejprve zkusíme cache
    cached = get_cached_reply(prompt, user)
    if cached:
        return cached
    # Pokud není v cache, vygenerujeme odpověď
    reply = llm(prompt)
    set_cached_reply(prompt, user, reply)
    return reply
