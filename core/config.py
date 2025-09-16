"""
Sophia – Centralizovaná konfigurace (core/config.py)
Všechny proměnné prostředí a cesty na jednom místě.
"""
import os
from starlette.config import Config

# Cesta ke .env souboru (lze upravit podle potřeby)
ENV_PATH = os.environ.get("SOPHIA_ENV_PATH", ".env")
config = Config(ENV_PATH)

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', cast=str, default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', cast=str, default='')
SECRET_KEY = config('SECRET_KEY', cast=str, default='supersecretkey')

# Další globální cesty, např. k datům, logům, atd.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'logs')


# Přepínač testovacího režimu (dynamicky)
def is_test_mode():
	return os.environ.get('SOPHIA_TEST_MODE') == '1'

# Seznam admin emailů (oddělené čárkou nebo načítané z .env)
ADMIN_EMAILS = set(
	email.strip() for email in os.environ.get('SOPHIA_ADMIN_EMAILS', '').split(',') if email.strip()
)
