import yaml
import time
import os
from datetime import datetime

CONFIG_FILE = "config.yaml"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sophia_main.log")

def ensure_log_dir_exists():
    """Zajistí, že adresář pro logy existuje."""
    os.makedirs(LOG_DIR, exist_ok=True)

def log_message(message):
    """Zaznamená zprávu do hlavního logu Sophie."""
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {message}\n")
    print(message, flush=True) # Přidán flush=True

def load_config():
    """Načte konfiguraci ze souboru config.yaml."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        log_message("Konfigurace úspěšně načtena.")
        return config
    except FileNotFoundError:
        log_message(f"CHYBA: Konfigurační soubor '{CONFIG_FILE}' nebyl nalezen.")
        return None
    except yaml.YAMLError as e:
        log_message(f"CHYBA: Chyba při parsování konfiguračního souboru: {e}")
        return None

def main():
    """Hlavní funkce Sophie, implementující cyklus bdění a spánku."""
    log_message("Jádro Vědomí (main.py) se spouští.")

    config = load_config()
    if not config:
        log_message("Kritická chyba: Nelze načíst konfiguraci. Ukončuji běh.")
        exit(1)

    waking_duration = config.get('lifecycle', {}).get('waking_duration_seconds', 10)
    sleeping_duration = config.get('lifecycle', {}).get('sleeping_duration_seconds', 5)

    log_message("Zahajuji cyklus Bdění a Spánku.")

    while True:
        log_message("STAV: Bdění - Aktivní fáze.")
        time.sleep(waking_duration)

        log_message("STAV: Spánek - Fáze sebereflexe a konsolidace.")
        time.sleep(sleeping_duration)

if __name__ == "__main__":
    main()
