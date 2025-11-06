"""Standalone WebUI Dashboard Server

Runs ONLY the dashboard for monitoring the task queue.
Worker can run independently via autonomous_main.py

Usage:
    .venv/bin/python scripts/dashboard_server.py

Access:
    http://127.0.0.1:8000/dashboard
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from plugins.interface_webui import WebUIInterface

async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("dashboard_server")
    
    logger.info("🚀 Starting SOPHIA Dashboard Server")
    logger.info("📊 Dashboard: http://127.0.0.1:8000/dashboard")
    logger.info("📡 API: http://127.0.0.1:8000/api/tasks")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    
    # Create standalone WebUI instance
    webui = WebUIInterface()
    webui.setup({"host": "127.0.0.1", "port": 8000})
    
    await webui.start_server()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down dashboard server")

if __name__ == "__main__":
    asyncio.run(main())
