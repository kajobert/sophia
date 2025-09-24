import hashlib
import glob
import re
import socket
import urllib.request
from datetime import datetime, timedelta
import os


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


def check_recurring_errors(log_paths=None, time_window_hours=1, error_threshold=3):
    """
    Analyzes log files for recurring errors within a specific time window.
    If a recurring error is found, it searches for a solution in the knowledge base.
    If a solution is found, it logs a warning with a link to the solution.
    If no solution isfound, it creates a file with a template for a new knowledge base entry.
    """
    if log_paths is None:
        log_paths = ["sophia_main.log", "guardian.log"]

    error_patterns = {
        "ModuleNotFoundError": r"ModuleNotFoundError",
        "TypeError": r"TypeError: 'coroutine' object is not awaitable",
        "TimeoutError": r"TimeoutError",
        "DefaultCredentialsError": r"DefaultCredentialsError",
    }

    keyword_map = {
        "ModuleNotFoundError": ["dependency", "závislostí", "ModuleNotFoundError"],
        "TypeError": ["async", "sync", "asynchronního", "TypeError"],
        "TimeoutError": ["timeout", "API", "službách"],
        "DefaultCredentialsError": [
            "credentials",
            "API klíč",
            "DefaultCredentialsError",
        ],
    }

    now = datetime.now()
    time_window = timedelta(hours=time_window_hours)
    error_counts = {key: [] for key in error_patterns}

    for log_path in log_paths:
        if not os.path.exists(log_path):
            # Try looking in the logs/ directory as a fallback
            if os.path.exists(f"logs/{log_path}"):
                log_path = f"logs/{log_path}"
            else:
                continue

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # Simple regex for timestamp, assuming format 'YYYY-MM-DD HH:MM:SS'
                    match = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    if not match:
                        continue

                    log_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    if now - log_time > time_window:
                        continue

                    for error_name, pattern in error_patterns.items():
                        if re.search(pattern, line):
                            error_counts[error_name].append(line)
        except Exception as e:
            print(f"Error reading log file {log_path}: {e}")

    for error_name, errors in error_counts.items():
        if len(errors) > error_threshold:
            # Chronic problem detected
            try:
                with open("docs/KNOWLEDGE_BASE.md", "r", encoding="utf-8") as f:
                    kb_content = f.read()

                found_solution = False
                for keyword in keyword_map[error_name]:
                    if re.search(keyword, kb_content, re.IGNORECASE):
                        # Find the most relevant topic heading
                        # This is a simple implementation, could be improved with better NLP
                        topic_headers = re.findall(r"### Téma: (.*)", kb_content)
                        for header in topic_headers:
                            if re.search(keyword, header, re.IGNORECASE):
                                anchor = "#" + header.lower().strip().replace(
                                    " ", "-"
                                ).replace('"', "").replace("(", "").replace(")", "")
                                print(
                                    f"WARNING: Detected recurring '{error_name}'. This issue is documented. See solution at: docs/KNOWLEDGE_BASE.md{anchor}"
                                )
                                found_solution = True
                                break
                        if found_solution:
                            break

                if not found_solution:
                    issue_filename = "NEW_ISSUE_TO_DOCUMENT.md"
                    with open(issue_filename, "w", encoding="utf-8") as f:
                        f.write(f"""# NOVÝ PROBLÉM K ZADOKUMENTOVÁNÍ

**Chyba**: {error_name}
**Počet výskytů za poslední hodinu**: {len(errors)}

**Příkladové logy:**
```
{"".join(errors[:3])}
```

## Template pro Znalostní Bázi (`docs/KNOWLEDGE_BASE.md`)

### Téma: [Stručný popis tématu týkající se '{error_name}']
**Datum**: {datetime.now().strftime("%Y-%m-%d")}
**Autor**: Guardian Monitor
**Kontext**: [Popiš, za jakých okolností se chyba vyskytla. Automaticky detekováno v log souborech.]
**Zjištění/Rozhodnutí**: [Jaký byl problém a jaké je navrhované nebo implementované řešení?]
**Důvod**: [Proč bylo toto řešení zvoleno?]
**Dopad**: [Jaký dopad má řešení na projekt?]
""")
                    print(
                        f"CRITICAL: Detected recurring '{error_name}' with no documented solution. Created '{issue_filename}' for documentation."
                    )

            except FileNotFoundError:
                print("ERROR: Knowledge base file 'docs/KNOWLEDGE_BASE.md' not found.")


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
