"""SOPHIA AMI Worker with WebUI Dashboard

Runs the 24/7 autonomous worker with monitoring dashboard.

Usage:
    .venv/bin/python scripts/autonomous_worker_with_dashboard.py

Dashboard:
    http://127.0.0.1:8000/dashboard
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# DO NOT disable interactive plugins - we need WebUI for dashboard
# Only disable them for headless worker in autonomous_main.py

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.simple_persistent_queue import SimplePersistentQueue
from core.kernel import Kernel
from core.kernel_worker import KernelWorker


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("worker_dashboard")

    # Ensure data dir exists
    os.makedirs(".data", exist_ok=True)

    queue = SimplePersistentQueue(db_path=".data/tasks.sqlite")

    logger.info("🚀 Starting SOPHIA AMI Worker with Dashboard")
    logger.info(f"📊 Dashboard available at: http://127.0.0.1:8000/dashboard")
    logger.info(f"📋 Pending tasks in queue: {queue.pending_count()}")
    
    # Initialize kernel with WebUI enabled (interface plugins allowed)
    # Note: We still run in offline mode for LLM calls
    kernel = Kernel(use_event_driven=False, offline_mode=True)
    
    # WebUI will start automatically when interface plugins execute
    logger.info("🌐 WebUI will be available shortly...")
    
    # Start worker
    worker = KernelWorker(kernel=kernel, queue=queue)
    worker_task = asyncio.create_task(worker.run())

    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Worker cancelled, shutting down")


if __name__ == "__main__":
    asyncio.run(main())
