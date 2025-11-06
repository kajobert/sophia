"""Simple supervisor to run the persistent queue and kernel worker 24/7.

Usage (WSL):
  .venv/bin/python scripts/autonomous_main.py

This script seeds a simple self-test task on startup so you can observe behavior
immediately. For production use, replace seeding with a Planner that inserts
real tasks into the queue.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# CRITICAL: Set environment variables BEFORE importing Kernel
# This ensures the worker runs in headless mode without interactive plugins
os.environ['SOPHIA_DISABLE_INTERACTIVE_PLUGINS'] = '1'

# Ensure project root is on sys.path when run directly from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.simple_persistent_queue import SimplePersistentQueue
from core.kernel import Kernel
from core.kernel_worker import KernelWorker


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("autonomous_main")

    # Ensure data dir exists
    os.makedirs(".data", exist_ok=True)

    queue = SimplePersistentQueue(db_path=".data/tasks.sqlite")

    # Seed a simple task if queue is empty
    if queue.pending_count() == 0:
        logger.info("Seeding self-test task into queue")
        queue.enqueue({"instruction": "Say hello and run a small self-test."}, priority=50)

    # CRITICAL: Worker MUST run in offline mode (local LLM only) for MVP
    # This prevents accidental API calls to cloud services during development
    logger.info("🔒 Worker running in OFFLINE MODE (local LLM only)")
    
    kernel = Kernel(use_event_driven=False, offline_mode=True)
    worker = KernelWorker(kernel=kernel, queue=queue)

    worker_task = asyncio.create_task(worker.run())

    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Worker cancelled, shutting down")


if __name__ == "__main__":
    asyncio.run(main())
