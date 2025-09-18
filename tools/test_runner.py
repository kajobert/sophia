import subprocess
import json
import os
import logging
import sys

REPORT_FILE = ".report.json"

def run_tests_and_get_results(target_path=None):
    """
    Spustí pytest na konkrétní cestě nebo v celém projektu,
    vygeneruje JSON report a vrátí strukturovaná data o selháních.
    """
    logging.info("Spouštím testovací sadu a generuji JSON report...")

    command = [
        sys.executable, "-m", "pytest",
        "--json-report", f"--json-report-file={REPORT_FILE}",
        "-p", "no:cacheprovider",
    ]
    if target_path:
        command.append(target_path)

    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    subprocess.run(command, capture_output=True, text=True, env=env)

    if not os.path.exists(REPORT_FILE):
        logging.error("JSON report nebyl vygenerován. Testy pravděpodobně selhaly fatálně.")
        return None

    try:
        with open(REPORT_FILE, 'r') as f:
            report = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logging.error("Nepodařilo se načíst nebo naparsovat JSON report.")
        return None
    finally:
        if os.path.exists(REPORT_FILE):
            os.remove(REPORT_FILE)

    if report.get('summary', {}).get('failed', 0) == 0:
        logging.info("Všechny testy prošly úspěšně.")
        return []

    failed_tests = []
    for test in report.get('tests', []):
        if test.get('outcome') == 'failed':
            failed_tests.append({
                "nodeid": test.get('nodeid'),
                "error": test.get('longrepr'),
                "stdout": test.get('stdout'),
                "stderr": test.get('stderr'),
            })

    logging.warning(f"Nalezeno {len(failed_tests)} selhávajících testů.")
    return failed_tests

if __name__ == '__main__':
    # Příklad použití
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Můžete spustit s argumentem, např. python tools/test_runner.py tests/test_api.py
    path_to_test = sys.argv[1] if len(sys.argv) > 1 else None

    failures = run_tests_and_get_results(target_path=path_to_test)

    if failures is not None:
        if not failures:
            print("Všechny testy na zadané cestě prošly.")
        else:
            print("Detaily selhání:")
            for failure in failures:
                print(json.dumps(failure, indent=2))
    else:
        print("Došlo k chybě při spouštění testů.")
