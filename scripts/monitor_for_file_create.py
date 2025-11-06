"""Monitor logs and filesystem for the creation of a target file performed by Sophia.

Usage: run this after enqueueing the test task. The script will wait up to `timeout` seconds
for the file to appear and will tail `logs/autonomous.log` (if present) to show planner/kernel output.
"""
import time
from pathlib import Path
import argparse


def tail_file_lines(path: Path, since=0):
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(since)
            data = f.read()
            return data, f.tell()
    except FileNotFoundError:
        return "", since


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="scripts/tui_by_sophia.py")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--log", default="logs/autonomous.log")
    args = parser.parse_args()

    target = Path(args.target)
    log_path = Path(args.log)

    print(f"Monitoring for file: {target} (timeout {args.timeout}s)")
    start = time.time()
    last_pos = 0
    while time.time() - start < args.timeout:
        if target.exists():
            print(f"SUCCESS: File created at: {target.resolve()}")
            try:
                print("---- File content preview ----")
                print(target.read_text(encoding="utf-8", errors="replace")[:1000])
            except Exception as e:
                print(f"Could not read file: {e}")
            return 0

        # tail logs and print planner-relevant lines
        logs, last_pos = tail_file_lines(log_path, since=last_pos)
        if logs:
            # print only planner/kernel lines to reduce noise
            for ln in logs.splitlines():
                if "planner" in ln.lower() or "planner failed" in ln.lower() or "create_plan" in ln or "No valid plan" in ln or "Planner" in ln or "Task" in ln:
                    print(ln)

        time.sleep(1)

    print(f"TIMEOUT: File {target} was not created within {args.timeout} seconds.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Monitor logs and filesystem for the creation of a file by Sophia.
Usage: python3 scripts/monitor_for_file_create.py --path scripts/tui_by_sophia.py --timeout 180
"""
import argparse
import time
import os
from pathlib import Path

LOG_FILE = "logs/autonomous.log"


def tail_log_for_phrase(log_path: str, phrase: str, timeout: int = 120):
    start = time.time()
    seen = set()
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            # Seek to end to watch new lines
            f.seek(0, os.SEEK_END)
            while time.time() - start < timeout:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                print(line.rstrip())
                if phrase in line:
                    return True
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")
        return False
    return False


def wait_for_file(path: str, timeout: int = 120):
    start = time.time()
    p = Path(path)
    while time.time() - start < timeout:
        if p.exists():
            print(f"Found file: {path}")
            return True
        time.sleep(0.5)
    print(f"Timeout waiting for file: {path}")
    return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="Path to expected file (relative to repo root)")
    ap.add_argument("--timeout", type=int, default=180, help="Timeout seconds")
    args = ap.parse_args()

    target = args.path
    timeout = args.timeout

    print(f"Watching logs for planner success and waiting up to {timeout}s for file {target}")

    # Start both checks concurrently: we loop and print new log lines and check for file
    start = time.time()
    log_path = LOG_FILE
    found = False
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
            lf.seek(0, os.SEEK_END)
            while time.time() - start < timeout:
                line = lf.readline()
                if not line:
                    # check for file
                    if Path(target).exists():
                        print(f"Success: file created: {target}")
                        found = True
                        break
                    time.sleep(0.5)
                    continue
                print(line.rstrip())
                # Quick heuristic: planner logged that a plan was found or kernel executed a write
                if "planner_failed" in line or "No valid plan" in line or "No plan" in line:
                    # show but continue
                    pass
                if "write_file" in line or "Successfully wrote" in line or "wrote" in line:
                    # likely success; also verify file exists
                    if Path(target).exists():
                        print(f"Detected write in logs and file exists: {target}")
                        found = True
                        break
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")

    if not found:
        # final file check
        if Path(target).exists():
            print(f"File exists: {target}")
            found = True

    if found:
        print("Monitor: SUCCESS")
        raise SystemExit(0)
    else:
        print("Monitor: FAILURE")
        raise SystemExit(2)
