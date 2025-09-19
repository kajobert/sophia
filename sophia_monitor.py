import hashlib
import glob
import re
import socket
import urllib.request


# --- Funkce pro test: detekce crash v logu ---
def check_backend_crash_log(log_path, lines=10):
    """Vrací dict s posledními řádky a nalezenými chybovými vzory (ImportError, Traceback)."""
    result = {"last_lines": [], "error_matches": []}
    patterns = [r"ImportError", r"Traceback"]
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            log_lines = f.readlines()[-lines:]
        result["last_lines"] = log_lines
        for i, line in enumerate(log_lines):
            for pat in patterns:
                if re.search(pat, line):
                    result["error_matches"].append((i, line.strip(), pat))
        return result
    except Exception:
        return result


"""
Sophia Monitor: Pokročilé kontroly pro guardian.py

Tento modul obsahuje všechny pokročilé, bezpečnostní a provozní kontroly, které mohou být volány z guardian.py nebo samostatně.

====================
PLÁNOVANÉ A EXISTUJÍCÍ KONTROLY
====================

**Existující kontroly:**
  - check_integrity():
      Kontrola integrity všech .py, .yaml, .env, .sh, .txt v rootu, core/, agents/ (SHA256 hash).
  - scan_logs_for_errors():
      Prohledá logy a detekuje opakované výskyty chybových hlášek (ERROR, CRITICAL, Traceback, Chyba, VAROVÁNÍ).
  - check_internet_connectivity():
      Ověří dostupnost internetu pokusem o HTTP request.
  - check_dns_resolution():
      Ověří funkčnost DNS překladu.

**Plánované kontroly (TODO):**
  - check_disk_usage():
      Kontrola volného místa na disku, případně rotace/smazání logů.
  - check_cpu_usage():
      Detekce přetížení CPU, případně upozornění nebo restart služby.
  - check_memory_usage():
      Kontrola využití RAM, případně upozornění nebo restart služby.
  - check_ssl_certificates():
      Ověření platnosti SSL certifikátů (např. pro web API).
  - check_backup_status():
      Kontrola, zda proběhly zálohy a jsou dostupné.
  - check_file_permissions():
      Ověření správných oprávnění u klíčových souborů.
  - check_process_health():
      Kontrola běhu klíčových procesů (např. Celery, Redis, backend).
  - check_external_services():
      Ověření dostupnosti externích API/služeb (např. LLM, cloud storage).

Každá kontrola by měla být samostatná funkce, snadno volatelná a testovatelná.
"""


def check_integrity():
    """Kontrola integrity všech .py, .yaml, .env, .sh, .txt v rootu, core/, agents/ (SHA256 hash)."""
    files = set()
    files.update(glob.glob("*.py"))
    files.update(glob.glob("core/*.py"))
    files.update(glob.glob("agents/*.py"))
    files.update(glob.glob("*.yaml"))
    files.update(glob.glob("*.env"))
    files.update(glob.glob("*.sh"))
    files.update(glob.glob("*.txt"))
    results = {}
    for path in sorted(files):
        try:
            with open(path, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            results[path] = h
        except Exception:
            results[path] = None
    return results


def scan_logs_for_errors(log_files=None, patterns=None, min_count=3):
    """Prohledá logy a detekuje opakované výskyty chybových hlášek."""
    if log_files is None:
        log_files = ["logs/guardian.log", "logs/sophia_main.log", "logs/audit.log"]
    if patterns is None:
        patterns = [r"ERROR", r"CRITICAL", r"Traceback", r"Chyba", r"VAROVÁNÍ"]
    error_counts = {}
    for log_path in log_files:
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pat in patterns:
                    count = len(re.findall(pat, content, re.IGNORECASE))
                    if count >= min_count:
                        error_counts[(log_path, pat)] = count
        except Exception:
            continue
    return error_counts


def check_internet_connectivity(url="https://www.google.com", timeout=5):
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


def check_dns_resolution(host="www.google.com"):
    try:
        socket.gethostbyname(host)
        return True
    except Exception:
        return False


# Další kontroly lze přidávat zde (CPU, disk, certifikáty, zálohy...)

if __name__ == "__main__":
    print("--- INTEGRITY ---")
    for path, h in check_integrity().items():
        print(f"{path}: {h}")
    print("\n--- LOG ERRORS ---")
    for (log, pat), count in scan_logs_for_errors().items():
        print(f"{log}: {pat} -> {count}")
    print("\n--- NETWORK ---")
    print("Internet:", check_internet_connectivity())
    print("DNS:", check_dns_resolution())
