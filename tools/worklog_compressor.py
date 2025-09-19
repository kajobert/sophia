import os
import re
import subprocess
import sys
from datetime import datetime

# --- Configuration ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKLOG_PATH = os.path.join(ROOT_DIR, "WORKLOG.md")
COMPRESSED_WORKLOG_PATH = os.path.join(ROOT_DIR, "WORKLOG_COMPRESSED.md")
LINE_THRESHOLD = 500
WORKLOG_TEMPLATE = """\
# Sophia V3 - Pracovní Deník (Work Log)

Tento dokument slouží jako detailní záznam o postupu vývoje projektu Sophia V3. Každý AI programátor je povinen zde dokumentovat svou práci.

---

### Šablona Záznamu

```
**Timestamp:** YYYY-MM-DD HH:MM:SS
**Agent:** [Jméno Agenta, např. Jules]
**Task ID:** [Číslo úkolu z PROJECT_SOPHIA_V3.md, např. 1.1]

**Cíl Úkolu:**
- [Stručný popis cíle]

**Postup a Klíčové Kroky:**
1.  [Krok 1]
2.  [Krok 2]
3.  ...

**Problémy a Překážky:**
- [Popis problému, se kterým se agent setkal]

**Navržené Řešení:**
- [Jak byl problém vyřešen]

**Nápady a Postřehy:**
- [Jakékoliv myšlenky na vylepšení, které agenta napadly během práce]

**Stav:** [Probíhá / Dokončeno / Zablokováno]
```
"""
COMPRESSED_LOG_HEADER = """\
# Komprimovaný Pracovní Deník (WORKLOG_COMPRESSED.md)

Tento soubor obsahuje automaticky generované souhrny z `WORKLOG.md`.
Je navržen pro rychlou orientaci v historii projektu bez nutnosti procházet detailní záznamy.

**Tento soubor neupravujte ručně.** Je přegenerován spuštěním skriptu `tools/worklog_compressor.py`.

---
"""

# --- Helper Functions ---


def print_color(text, color_code):
    """Prints text in a given color."""
    print(f"\033[{color_code}m{text}\033[0m")


# --- Core Logic ---


def should_compress():
    """Checks if the worklog file exists and exceeds the line threshold."""
    if not os.path.exists(WORKLOG_PATH):
        print_color(f"'{WORKLOG_PATH}' nenalezen. Není co komprimovat.", "93")  # Yellow
        return False

    with open(WORKLOG_PATH, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f)

    if line_count <= LINE_THRESHOLD:
        print_color(
            f"Worklog má {line_count} řádků (práh je {LINE_THRESHOLD}). Komprese není nutná.",
            "92",
        )  # Green
        return False

    print_color(f"Worklog má {line_count} řádků. Spouštím kompresi...", "94")  # Blue
    return True


def run_tests():
    """
    Runs the project's pytest suite to verify stability.
    Returns True if all tests pass, False otherwise.
    """
    print_color("\n--- Spouštím ověřovací testy ---", "96")  # Cyan
    try:
        # We need to set PYTHONPATH to include the root directory for imports to work correctly.
        env = os.environ.copy()
        env["PYTHONPATH"] = ROOT_DIR

        subprocess.run(
            [sys.executable, "-m", "pytest"],
            cwd=ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        print_color("Všechny testy úspěšně prošly.", "92")  # Green
        return True
    except subprocess.CalledProcessError as e:
        print_color("--- Selhání testů! ---", "91")  # Red
        print(e.stdout)
        print(e.stderr)
        print_color(
            "Komprese byla přerušena kvůli selhání testů. Opravte testy a zkuste to znovu.",
            "91",
        )
        return False
    except FileNotFoundError:
        print_color(
            "Příkaz 'pytest' nenalezen. Ujistěte se, že je nainstalován a v cestě.",
            "91",
        )
        return False


def summarize_worklog_entry(entry_text):
    """
    Summarizes a single worklog entry.

    NOTE: This is a simplified, rule-based summarization.
    For a more advanced summary, this function should be replaced
    with a call to an LLM (e.g., using core.gemini_llm_adapter).
    """
    # Extract key fields using regex
    timestamp = re.search(r"\*\*Timestamp:\*\* (.*)", entry_text)
    task_id = re.search(r"\*\*Task ID:\*\* (.*)", entry_text)
    goal = re.search(r"\*\*Cíl Úkolu:\*\*\n- (.*)", entry_text)
    status = re.search(r"\*\*Stav:\*\* (.*)", entry_text)

    # Format the summary line
    summary_parts = []
    if timestamp:
        summary_parts.append(f"**[{timestamp.group(1).strip()}]**")
    if task_id:
        summary_parts.append(f"(Task: `{task_id.group(1).strip()}`)")
    if goal:
        summary_parts.append(f"- {goal.group(1).strip()}")
    if status:
        summary_parts.append(f"-> **{status.group(1).strip()}**")

    return " ".join(summary_parts) if summary_parts else None


def generate_summary(worklog_content):
    """
    Parses the full worklog and generates a summary text.
    """
    print_color("\n--- Generuji souhrn ---", "96")
    entries = worklog_content.split("---")
    summaries = []

    for entry in entries:
        if (
            "**Timestamp:**" in entry and "**Agent:**" in entry
        ):  # Basic check for a valid entry
            summary_line = summarize_worklog_entry(entry)
            if summary_line:
                summaries.append(f"* {summary_line}")

    if not summaries:
        print_color("Nebyly nalezeny žádné platné záznamy k sumarizaci.", "93")
        return None

    print_color(f"Úspěšně sumarizováno {len(summaries)} záznamů.", "92")
    return "\n".join(summaries)


def update_compressed_log(summary_text):
    """Appends the new summary to the compressed log file."""
    print_color(f"\n--- Aktualizuji '{COMPRESSED_WORKLOG_PATH}' ---", "96")

    # Prepend header if the file doesn't exist
    if not os.path.exists(COMPRESSED_WORKLOG_PATH):
        with open(COMPRESSED_WORKLOG_PATH, "w", encoding="utf-8") as f:
            f.write(COMPRESSED_LOG_HEADER)
            f.write("\n")

    with open(COMPRESSED_WORKLOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n## Souhrn z {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(summary_text)
        f.write("\n")

    print_color("Komprimovaný log byl úspěšně aktualizován.", "92")


def reset_worklog():
    """Resets the original worklog file to its template content."""
    print_color(f"\n--- Resetuji '{WORKLOG_PATH}' ---", "96")
    with open(WORKLOG_PATH, "w", encoding="utf-8") as f:
        f.write(WORKLOG_TEMPLATE)
    print_color("Původní worklog byl úspěšně resetován.", "92")


def main():
    """Main function to run the compression process."""
    print_color("=" * 50, "95")
    print_color("      SKRIPT PRO KOMPRESI WORKLOGU", "95")
    print_color("=" * 50, "95")

    if not should_compress():
        return

    if not run_tests():
        return

    try:
        with open(WORKLOG_PATH, "r", encoding="utf-8") as f:
            worklog_content = f.read()
    except Exception as e:
        print_color(f"Chyba při čtení '{WORKLOG_PATH}': {e}", "91")
        return

    summary = generate_summary(worklog_content)

    if summary:
        update_compressed_log(summary)
        reset_worklog()
        print_color("\nKomprese worklogu byla úspěšně dokončena!", "92")
    else:
        print_color("\nKomprese byla přerušena, protože nebylo co sumarizovat.", "93")


if __name__ == "__main__":
    main()
