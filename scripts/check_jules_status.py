#!/usr/bin/env python3
"""Check Jules session status"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import asyncio
from core.context import SharedContext
from plugins.tool_jules import JulesAPITool
from dotenv import load_dotenv
import os

async def check_status(session_id: str):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("check")
    
    jules = JulesAPITool()
    load_dotenv()
    jules.setup({"jules_api_key": os.getenv("JULES_API_KEY"), "logger": logger, "all_plugins": {}})
    
    context = SharedContext(session_id="check", current_state="CHECK", logger=logger)
    
    session = jules.get_session(context, session_id)
    
    print(f"\n{'='*60}")
    print(f"Jules Session: {session_id}")
    print(f"{'='*60}")
    print(f"Title: {session.title}")
    print(f"State: {session.state}")
    print(f"Created: {session.create_time}")
    print(f"Updated: {session.update_time}")
    print(f"Prompt: {session.prompt[:100]}..." if session.prompt else "No prompt")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "sessions/2258538751178656482"
    asyncio.run(check_status(session_id))
