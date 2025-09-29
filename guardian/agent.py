# Guardian Agent - Strážce
# Tento skript monitoruje systémové prostředky a loguje potenciální problémy.

import psutil
import logging
import time
from datetime import datetime

# --- Konfigurace ---
LOG_FILE = "guardian.log"
DISK_THRESHOLD_PERCENT = 90  # Procentuální práh pro varování o disku
MEMORY_THRESHOLD_MB = 1024   # Práh v MB pro varování o paměti

# --- Nastavení logování ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Zobrazí logy i v konzoli
    ]
)

def get_human_readable_size(size_bytes):
    """Převádí velikost v bajtech na čitelnější formát (KB, MB, GB)."""
    if size_bytes is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size_bytes >= power and n < len(power_labels) -1 :
        size_bytes /= power
        n += 1
    return f"{size_bytes:.2f} {power_labels[n]}"


def check_disk_usage(path='/'):
    """Kontroluje využití disku a loguje informace."""
    try:
        usage = psutil.disk_usage(path)
        logging.info(f"Disk ({path}): Celkem: {get_human_readable_size(usage.total)}, Využito: {get_human_readable_size(usage.used)} ({usage.percent}%)")
        if usage.percent > DISK_THRESHOLD_PERCENT:
            logging.warning(f"Využití disku překročilo práh {DISK_THRESHOLD_PERCENT}%!")
    except FileNotFoundError:
        logging.error(f"Chyba: Adresář pro kontrolu disku '{path}' nebyl nalezen.")
    except Exception as e:
        logging.error(f"Nastala neočekávaná chyba při kontrole disku: {e}")


def check_memory_usage():
    """Kontroluje využití paměti a loguje informace."""
    try:
        mem = psutil.virtual_memory()
        available_mb = mem.available / (1024 * 1024)
        logging.info(f"Paměť: Celkem: {get_human_readable_size(mem.total)}, K dispozici: {get_human_readable_size(mem.available)} ({mem.percent}% využito)")
        if available_mb < MEMORY_THRESHOLD_MB:
            logging.warning(f"Dostupná paměť klesla pod práh {MEMORY_THRESHOLD_MB} MB!")
    except Exception as e:
        logging.error(f"Nastala neočekávaná chyba při kontrole paměti: {e}")

import os

# --- Dodatečná Konfigurace ---
FILE_DESCRIPTOR_THRESHOLD = 768 # Varovný práh (75% z limitu 1024)
PROCESS_FD_THRESHOLD = 256    # Práh pro logování jednotlivého procesu

def check_open_files():
    """
    Kontroluje počet otevřených souborových deskriptorů pro procesy
    běžící pod aktuálním uživatelem.
    """
    try:
        current_uid = os.getuid()
        total_fds = 0
        high_usage_procs = []

        for proc in psutil.process_iter(['pid', 'name', 'username', 'uids']):
            # Kontrolujeme pouze procesy patřící aktuálnímu uživateli
            if proc.info['uids'] and proc.info['uids'].real == current_uid:
                try:
                    num_fds = proc.num_fds()
                    total_fds += num_fds
                    if num_fds > PROCESS_FD_THRESHOLD:
                        high_usage_procs.append((proc.info['name'], proc.info['pid'], num_fds))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Proces mohl mezitím skončit, nebo k němu nemáme přístup
                    continue

        logging.info(f"Souborové deskriptory: Celkem otevřeno {total_fds} pro uživatele {psutil.Process().username()}.")

        if high_usage_procs:
            # Seřadíme procesy podle počtu deskriptorů sestupně
            high_usage_procs.sort(key=lambda x: x[2], reverse=True)
            log_message = "Procesy s vysokým využitím FD: " + ", ".join([f"{name}({pid}): {count}" for name, pid, count in high_usage_procs[:3]])
            logging.info(log_message)

        if total_fds > FILE_DESCRIPTOR_THRESHOLD:
            logging.warning(f"Celkový počet otevřených souborových deskriptorů ({total_fds}) překročil práh {FILE_DESCRIPTOR_THRESHOLD}!")

    except Exception as e:
        logging.error(f"Nastala neočekávaná chyba při kontrole souborových deskriptorů: {e}")


def main():
    """
    Hlavní funkce agenta. Spouští monitorovací smyčku.
    """
    logging.info("--- Projekt Strážce (Guardian) spuštěn ---")
    logging.info(f"Limit pro varování disku: {DISK_THRESHOLD_PERCENT}%")
    logging.info(f"Limit pro varování paměti: {MEMORY_THRESHOLD_MB} MB")
    logging.info(f"Limit pro varování FD: {FILE_DESCRIPTOR_THRESHOLD}")

    check_interval_seconds = 30

    while True:
        try:
            logging.info("=== Zahajuji nový cyklus kontrol ===")
            check_disk_usage()
            check_memory_usage()
            check_open_files()
            logging.info(f"=== Cyklus kontrol dokončen. Další za {check_interval_seconds} sekund. ===")
            time.sleep(check_interval_seconds)
        except KeyboardInterrupt:
            logging.info("--- Agent Strážce (Guardian) ukončen uživatelem. ---")
            break
        except Exception as e:
            logging.critical(f"V hlavní smyčce nastala kritická chyba: {e}")
            logging.info("Pokouším se pokračovat po krátké pauze.")
            time.sleep(check_interval_seconds)

if __name__ == "__main__":
    main()