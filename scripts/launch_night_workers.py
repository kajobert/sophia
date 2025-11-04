#!/usr/bin/env python3
"""
🌙 Launch Night Jules Workers
Launch multiple Jules workers for overnight research & development.
"""

import asyncio
import sys
import os
import requests
from pathlib import Path
from datetime import datetime

# Worker configurations
NIGHT_WORKERS = [
    {
        "name": "Documentation Scholar",
        "branch": "nomad/night-research-rich-best-practices",
        "task_file": "docs/tasks/JULES_TASK_RICH_RESEARCH.md",
        "priority": "HIGH",
        "description": "Research Rich library best practices and production patterns",
    },
    {
        "name": "AI UX Trends Analyst",
        "branch": "nomad/night-research-ai-ux-2025",
        "task_file": "docs/tasks/JULES_TASK_UX_TRENDS.md",
        "priority": "MEDIUM",
        "description": "Analyze competitive AI assistant interfaces and UX trends",
    },
    {
        "name": "GitHub Gems Hunter",
        "branch": "nomad/night-discover-tui-gems",
        "task_file": "docs/tasks/JULES_TASK_GITHUB_GEMS.md",
        "priority": "HIGH",
        "description": "Discover and analyze top GitHub TUI repositories",
    },
    {
        "name": "Documentation Auditor",
        "branch": "nomad/night-audit-our-docs",
        "task_file": "docs/tasks/JULES_TASK_DOCS_AUDIT.md",
        "priority": "MEDIUM",
        "description": "Audit documentation quality and create improvement plan",
    },
]


async def launch_worker(worker_config: dict) -> dict:
    """Launch a single Jules worker."""
    print(f"\n🚀 Launching: {worker_config['name']}")
    print(f"   Branch: {worker_config['branch']}")
    print(f"   Priority: {worker_config['priority']}")

    # Read task file
    task_file = Path(worker_config["task_file"])
    if not task_file.exists():
        print(f"   ❌ Task file not found: {task_file}")
        return {"success": False, "worker": worker_config["name"], "error": "Task file missing"}

    task_content = task_file.read_text()

    # Get Jules API key from environment
    api_key = os.getenv("JULES_API_KEY")
    if not api_key:
        print("   ❌ JULES_API_KEY not set in environment")
        return {"success": False, "worker": worker_config["name"], "error": "Missing API key"}

    # Jules API endpoint
    base_url = os.getenv("JULES_API_BASE_URL", "https://jules.corp.google.com/api/v1")

    try:
        # Create new session via direct API call
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "base_branch": "feature/jules-api-integration",
            "task_branch": worker_config["branch"],
            "instructions": task_content,
            "model": "gemini-2.0-flash-exp",
        }

        response = requests.post(f"{base_url}/sessions", headers=headers, json=payload, timeout=30)

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            session_id = result.get("session_id") or result.get("name", "").split("/")[-1]

            print(f"   ✅ Session created: {session_id}")
            print(f"   📊 Quota used: {result.get('quota_used', 'unknown')}/100")

            return {
                "success": True,
                "worker": worker_config["name"],
                "session_id": session_id,
                "branch": worker_config["branch"],
            }
        else:
            error_msg = response.text[:200] if response.text else "Unknown error"
            print(f"   ❌ Failed: HTTP {response.status_code}")
            print(f"   {error_msg}")
            return {
                "success": False,
                "worker": worker_config["name"],
                "error": f"HTTP {response.status_code}",
            }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "worker": worker_config["name"], "error": str(e)}


async def main():
    """Launch all night workers."""
    print("=" * 80)
    print("🌙 NIGHT JULES WORKERS LAUNCH SEQUENCE")
    print("=" * 80)
    print(f"\nLaunching {len(NIGHT_WORKERS)} workers for overnight research...")
    print("Each worker will work autonomously until task completion.")
    print("\n⚠️  Safety protocols enabled:")
    print("   - Only nomad/* branches")
    print("   - No master/feature branch modifications")
    print("   - Research & documentation only")

    # Skip interactive input if running in background (no TTY)
    import sys

    if sys.stdin.isatty():
        input("\n👉 Press ENTER to launch all workers, or Ctrl+C to cancel...")
    else:
        print("\n🤖 Running in background mode - auto-launching in 3 seconds...")
        await asyncio.sleep(3)

    # Launch all workers in parallel
    results = []
    for worker in NIGHT_WORKERS:
        result = await launch_worker(worker)
        results.append(result)
        await asyncio.sleep(2)  # Small delay between launches

    # Summary
    print("\n" + "=" * 80)
    print("📊 LAUNCH SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n✅ Successfully launched: {len(successful)}/{len(NIGHT_WORKERS)}")
    for result in successful:
        print(f"   • {result['worker']}")
        print(f"     Session: {result['session_id']}")
        print(f"     Branch: {result['branch']}")

    if failed:
        print(f"\n❌ Failed to launch: {len(failed)}")
        for result in failed:
            print(f"   • {result['worker']}: {result.get('error', 'Unknown error')}")

    print("\n" + "=" * 80)
    print("🌙 Workers are now running autonomously!")
    print("💤 Go to sleep - check results in the morning at 9:00 AM")
    print("📍 Track sessions: docs/JULES_ACTIVE_SESSIONS.md")
    print("=" * 80)

    # Update active sessions file
    if successful:
        update_active_sessions(successful)


def update_active_sessions(workers: list):
    """Update active sessions tracking file."""

    sessions_file = Path("docs/JULES_ACTIVE_SESSIONS.md")

    content = "# Jules Active Sessions\n\n"
    content += f"**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    content += f"## 🌙 Night Workers (Launched: {datetime.now().strftime('%H:%M')})\n\n"

    for worker in workers:
        content += f"### {worker['worker']}\n"
        content += f"- **Session ID:** `{worker['session_id']}`\n"
        content += f"- **Branch:** `{worker['branch']}`\n"
        content += "- **Status:** 🏃 RUNNING\n"
        content += "- **Check:** Morning 9:00 AM\n\n"

    sessions_file.write_text(content)
    print(f"\n📝 Updated: {sessions_file}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Launch cancelled by user")
        sys.exit(1)
