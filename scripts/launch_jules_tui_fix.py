#!/usr/bin/env python3
"""
🤖 Jules Task Launcher - TUI UX Fix

Spustí Jules session pro opravu TUI bez blikání.
Jules bude pracovat asynchronně v branch 'nomad/tui-uv-style-fix'.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from plugins.tool_jules import JulesAPITool
from core.context import SharedContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def launch_jules_tui_fix():
    """Launch Jules session for TUI fix task."""
    
    print("🤖 Launching Jules for TUI UX Fix...")
    print("=" * 60)
    
    # Initialize Jules tool
    jules = JulesAPITool()
    jules.setup({})
    
    # Verify API key
    if not jules.api_key:
        print("❌ ERROR: JULES_API_KEY not found in environment!")
        print("   Please set: export JULES_API_KEY='your-key'")
        return False
    
    print("✅ Jules API key found")
    
    # List existing sessions (check quota)
    print("\n📊 Checking current Jules usage...")
    try:
        context = SharedContext(
            session_id="jules-launcher",
            current_state="PLANNING",
            logger=logger,
            history=[],
            payload={}
        )
        
        result = await jules.list_sessions(context=context)
        sessions = result.get("sessions", [])
        print(f"   Current sessions today: {len(sessions)}/100")
        
        if len(sessions) >= 100:
            print("⚠️  WARNING: Daily quota exhausted!")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check sessions: {e}")
    
    # Read task description
    task_file = Path(__file__).parent / "docs" / "JULES_TASK_TUI_FIX.md"
    
    if not task_file.exists():
        print(f"❌ ERROR: Task file not found: {task_file}")
        return False
    
    task_description = task_file.read_text()
    print(f"✅ Task loaded from: {task_file.name}")
    
    # Create Jules session
    print("\n🚀 Creating Jules session...")
    print("   Task: Fix TUI flicker and layout issues")
    print("   Branch: nomad/tui-uv-style-fix")
    print("   Repo: ShotyCZ/sophia")
    
    try:
        session_result = await jules.create_session(
            context=context,
            prompt=task_description,
            source="sources/github/ShotyCZ/sophia",
            branch="nomad/tui-uv-style-fix",
            title="TUI UX Fix - UV Style No Flicker",
            auto_pr=True  # Auto-create PR when done
        )
        
        session_id = session_result.get("session_id")
        session_url = session_result.get("url", "N/A")
        
        print("\n✅ Jules session created successfully!")
        print("=" * 60)
        print(f"📋 Session ID: {session_id}")
        print(f"🔗 Monitor at: {session_url}")
        print("\n🤖 Jules is now working asynchronously on:")
        print("   • Fix Live mode flicker")
        print("   • Redirect stdout/stderr")
        print("   • Fix duplicate boot")
        print("   • Suppress warnings")
        print("   • Test all scenarios")
        print("\n⏱️  Estimated time: 2-4 hours")
        print("💬 You can continue chatting with Sophia while Jules works!")
        print("=" * 60)
        
        # Save session info
        info_file = Path(__file__).parent / "docs" / "JULES_ACTIVE_SESSIONS.md"
        with open(info_file, "a") as f:
            f.write(f"\n## Session: {session_id}\n")
            f.write(f"- **Created:** {asyncio.get_event_loop().time()}\n")
            f.write(f"- **Task:** TUI UX Fix\n")
            f.write(f"- **Branch:** nomad/tui-uv-style-fix\n")
            f.write(f"- **URL:** {session_url}\n")
        
        print(f"\n💾 Session info saved to: {info_file.name}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR creating Jules session: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await launch_jules_tui_fix()
    
    if success:
        print("\n🎉 SUCCESS! Jules is working in background.")
        print("👉 Switch back to feature branch:")
        print("   git checkout feature/jules-api-integration")
        print("\n👉 Continue chatting with Sophia:")
        print("   python run.py")
        sys.exit(0)
    else:
        print("\n❌ Failed to launch Jules session.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
