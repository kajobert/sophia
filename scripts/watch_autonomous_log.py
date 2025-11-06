"""Watch `logs/autonomous.log` and highlight important lines.

This script tails the autonomous log and writes a filtered `logs/autonomous_highlights.log`
containing ERRORs, Exceptions, and Tracebacks for quick triage. It also prints
new lines to stdout so it can be run interactively.
"""
import asyncio
import sys
from pathlib import Path


LOG_PATH = Path("logs/autonomous.log")
HIGHLIGHT_PATH = Path("logs/autonomous_highlights.log")


async def tail_file(path: Path):
    # Wait until file exists
    while not path.exists():
        await asyncio.sleep(0.2)

    with path.open("r", encoding="utf-8", errors="replace") as f:
        # Go to end of file
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.1)
                continue
            yield line


async def main():
    print(f"Watching {LOG_PATH} (highlights -> {HIGHLIGHT_PATH})")
    HIGHLIGHT_PATH.parent.mkdir(parents=True, exist_ok=True)

    async for line in tail_file(LOG_PATH):
        # Print the raw line so the user sees realtime output
        print(line, end="")

        # If line looks like an error, append to highlights
        if any(k in line for k in ("ERROR", "Exception", "Traceback", "CRITICAL")):
            try:
                with HIGHLIGHT_PATH.open("a", encoding="utf-8") as hf:
                    hf.write(line)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping log watcher")
        sys.exit(0)
