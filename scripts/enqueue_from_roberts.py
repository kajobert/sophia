"""Read `docs/roberts-notes.txt` and enqueue each non-empty line as a task.

This is a fast way to seed Sophia with ideas to try and benchmarks to run.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.simple_persistent_queue import SimplePersistentQueue


POSSIBLE_PATHS = [
    Path("docs/roberts-notes.txt"),
    Path("docs/roberts-notes.md"),
    Path("docs/ROBERTS_NOTES.txt"),
    Path("docs/roberts_notes.txt"),
]


def find_notes_file():
    for p in POSSIBLE_PATHS:
        if p.exists():
            return p
    return None


def main():
    notes = find_notes_file()
    if not notes:
        print("No roberts-notes file found in docs/. Create docs/roberts-notes.txt with one instruction per line.")
        sys.exit(1)

    q = SimplePersistentQueue(db_path=".data/tasks.sqlite")
    enqueued = 0
    # Read paragraphs (blocks separated by one or more blank lines) so
    # multi-line notes become a single task instead of multiple small ones.
    with notes.open("r", encoding="utf-8") as f:
        buffer_lines = []
        for raw in f:
            line = raw.rstrip("\n")
            # skip comment lines
            if line.strip().startswith("#"):
                continue

            if line.strip() == "":
                # blank line: flush buffer as one paragraph/task
                if buffer_lines:
                    paragraph = " ".join(l.strip() for l in buffer_lines if l.strip())
                    if paragraph:
                        payload = {
                            "instruction": paragraph,
                            "origin": "roberts_notes",
                            # By default, do not allow cloud calls for roberts notes processing.
                            "allow_cloud": False,
                        }
                        tid = q.enqueue(payload, priority=75)
                        enqueued += 1
                        print(f"Enqueued: {tid} -> {paragraph[:120]}")
                    buffer_lines = []
                continue

            buffer_lines.append(line)

        # flush remaining buffer
        if buffer_lines:
            paragraph = " ".join(l.strip() for l in buffer_lines if l.strip())
            if paragraph:
                payload = {
                    "instruction": paragraph,
                    "origin": "roberts_notes",
                    "allow_cloud": False,
                }
                tid = q.enqueue(payload, priority=75)
                enqueued += 1
                print(f"Enqueued: {tid} -> {paragraph[:120]}")

    print(f"Total enqueued: {enqueued}")


if __name__ == "__main__":
    main()
