"""Enqueue a single task into the SimplePersistentQueue from the command line.

Usage:
  .venv/bin/python scripts/enqueue_task.py "Refactor plugin X for clarity" --priority 50
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from core.simple_persistent_queue import SimplePersistentQueue


def main():
    parser = argparse.ArgumentParser(description="Enqueue a single instruction into Sophia's persistent queue")
    parser.add_argument("instruction", nargs="+", help="Instruction text to enqueue")
    parser.add_argument("--priority", type=int, default=100, help="Numeric priority (lower = higher priority)")
    args = parser.parse_args()

    instruction = " ".join(args.instruction)
    q = SimplePersistentQueue(db_path=".data/tasks.sqlite")
    tid = q.enqueue({"instruction": instruction}, priority=args.priority)
    print(f"Enqueued task id={tid} priority={args.priority}")


if __name__ == "__main__":
    main()
