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

    # Enable event-driven architecture for full plugin functionality
    # This allows cognitive_notes_reader, benchmark_runner, and other heartbeat plugins to run
    # NOTE: Dashboard (interface_webui) will be available at http://127.0.0.1:8000
    logger.info("🎯 Worker running with EVENT-DRIVEN architecture, OFFLINE mode, and DASHBOARD enabled")
    
    kernel = Kernel(use_event_driven=True, offline_mode=True)
    
    # Dashboard is automatically started by Kernel plugins (interface_webui)
    # No need to manually start it here
    
    worker = KernelWorker(kernel=kernel, queue=queue)

    worker_task = asyncio.create_task(worker.run())

    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Worker cancelled, shutting down")


if __name__ == "__main__":
    asyncio.run(main())
