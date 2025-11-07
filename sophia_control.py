#!/usr/bin/env python3
"""
SOPHIA Control Center - Advanced TUI Menu

Interactive terminal menu for managing SOPHIA system.
Provides easy access to all tools, tests, and utilities.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import json

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    """Print SOPHIA header."""
    clear_screen()
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                 🤖 SOPHIA CONTROL CENTER                   ║")
    print("║                    AMI 1.0 - Management TUI                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

def run_command(cmd: str, description: str = None, background: bool = False):
    """Execute shell command and show output."""
    if description:
        print(f"\n{Colors.OKCYAN}▶ {description}{Colors.ENDC}")
    
    print(f"{Colors.OKBLUE}$ {cmd}{Colors.ENDC}\n")
    
    if background:
        subprocess.Popen(cmd, shell=True)
        print(f"{Colors.OKGREEN}✅ Started in background{Colors.ENDC}")
    else:
        result = subprocess.run(cmd, shell=True)
        if result.returncode == 0:
            print(f"\n{Colors.OKGREEN}✅ Success{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}❌ Failed with code {result.returncode}{Colors.ENDC}")
    
    input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.ENDC}")

def show_status():
    """Show SOPHIA system status."""
    print(f"\n{Colors.BOLD}📊 System Status:{Colors.ENDC}\n")
    
    # Check if SOPHIA is running
    result = subprocess.run(
        "ps aux | grep 'python run.py' | grep -v grep",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(f"{Colors.OKGREEN}✅ SOPHIA is running{Colors.ENDC}")
        print(f"   {result.stdout.strip()}")
    else:
        print(f"{Colors.WARNING}⚠️  SOPHIA is not running{Colors.ENDC}")
    
    # Check Dashboard
    result = subprocess.run(
        "curl -s http://127.0.0.1:8000/api/stats 2>/dev/null",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        try:
            stats = json.loads(result.stdout)
            print(f"\n{Colors.OKGREEN}✅ Dashboard is accessible{Colors.ENDC}")
            print(f"   📌 Plugins: {stats.get('plugin_count', 'N/A')}")
            print(f"   📋 Pending tasks: {stats.get('pending_count', 'N/A')}")
            print(f"   ✅ Done tasks: {stats.get('done_count', 'N/A')}")
        except:
            print(f"{Colors.WARNING}⚠️  Dashboard returned invalid data{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️  Dashboard is not accessible{Colors.ENDC}")
    
    # Check Ollama
    result = subprocess.run(
        "curl -s http://localhost:11434/api/tags 2>/dev/null",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        try:
            data = json.loads(result.stdout)
            models = data.get('models', [])
            print(f"\n{Colors.OKGREEN}✅ Ollama is running{Colors.ENDC}")
            print(f"   🤖 Models: {len(models)}")
            for model in models[:3]:
                print(f"      • {model['name']}")
        except:
            pass
    else:
        print(f"{Colors.WARNING}⚠️  Ollama is not accessible{Colors.ENDC}")

def main_menu():
    """Display and handle main menu."""
    while True:
        print_header()
        show_status()
        
        print(f"\n{Colors.BOLD}📋 Main Menu:{Colors.ENDC}\n")
        
        print(f"{Colors.HEADER}1. 🚀 SOPHIA Control{Colors.ENDC}")
        print("   11. Start SOPHIA (--once mode)")
        print("   12. Start SOPHIA (daemon mode)")
        print("   13. Start SOPHIA with WebUI")
        print("   14. Stop SOPHIA")
        print("   15. Restart SOPHIA")
        print("   16. View logs (tail -f)")
        
        print(f"\n{Colors.HEADER}2. 🧪 Testing & Debugging{Colors.ENDC}")
        print("   21. Run all tests")
        print("   22. Run Dashboard E2E tests")
        print("   23. Interactive Dashboard test")
        print("   24. Debug Dashboard (with hooks)")
        print("   25. Test model escalation")
        print("   26. Run plugin tests")
        
        print(f"\n{Colors.HEADER}3. 🔍 Monitoring & Logs{Colors.ENDC}")
        print("   31. View SOPHIA logs")
        print("   32. View error logs only")
        print("   33. Monitor task queue")
        print("   34. Monitor system resources")
        print("   35. Check database status")
        
        print(f"\n{Colors.HEADER}4. 🛠️ Development Tools{Colors.ENDC}")
        print("   41. Open Dashboard in browser")
        print("   42. Generate screenshots")
        print("   43. Backup database")
        print("   44. Clear task queue")
        print("   45. Reset self-improvement")
        print("   46. Run linter (ruff)")
        
        print(f"\n{Colors.HEADER}5. 🌐 Ollama Management{Colors.ENDC}")
        print("   51. List models")
        print("   52. Pull new model")
        print("   53. Test llama3.1:8b")
        print("   54. Test qwen2.5:14b")
        print("   55. Ollama status")
        
        print(f"\n{Colors.HEADER}6. 📊 Dashboard Tools{Colors.ENDC}")
        print("   61. Open Dashboard")
        print("   62. Test all API endpoints")
        print("   63. Send test message to Chat")
        print("   64. Export Dashboard data")
        
        print(f"\n{Colors.HEADER}7. 🔧 Advanced{Colors.ENDC}")
        print("   71. Python shell with SOPHIA context")
        print("   72. Database shell (sqlite3)")
        print("   73. Git status & commit")
        print("   74. Create backup")
        print("   75. System diagnostics")
        
        print(f"\n{Colors.FAIL}0. Exit{Colors.ENDC}")
        
        choice = input(f"\n{Colors.BOLD}Select option: {Colors.ENDC}").strip()
        
        # SOPHIA Control
        if choice == "11":
            run_command(".venv/bin/python run.py --once", "Starting SOPHIA in --once mode")
        elif choice == "12":
            run_command("nohup .venv/bin/python run.py > /tmp/sophia.log 2>&1 &", "Starting SOPHIA daemon", background=True)
        elif choice == "13":
            run_command("nohup .venv/bin/python run.py --ui classic > /tmp/sophia_webui.log 2>&1 &", "Starting SOPHIA with WebUI", background=True)
        elif choice == "14":
            run_command("pkill -f 'python run.py'", "Stopping SOPHIA")
        elif choice == "15":
            run_command("pkill -f 'python run.py' && sleep 2 && nohup .venv/bin/python run.py --ui classic > /tmp/sophia.log 2>&1 &", "Restarting SOPHIA", background=True)
        elif choice == "16":
            run_command("tail -f logs/sophia.log", "Following SOPHIA logs (Ctrl+C to stop)")
        
        # Testing & Debugging
        elif choice == "21":
            run_command(".venv/bin/pytest -v", "Running all tests")
        elif choice == "22":
            run_command(".venv/bin/pytest test_dashboard_e2e.py -v", "Running Dashboard E2E tests")
        elif choice == "23":
            run_command(".venv/bin/python dashboard_interactive_test.py", "Interactive Dashboard test")
        elif choice == "24":
            run_command(".venv/bin/python dashboard_debug.py --scenario all --interactive", "Dashboard debugger with hooks")
        elif choice == "25":
            run_command(".venv/bin/python run.py --once --input 'Jaké jsou tvé aktuální schopnosti?'", "Testing model escalation")
        elif choice == "26":
            run_command(".venv/bin/pytest tests/ -v -k plugin", "Running plugin tests")
        
        # Monitoring & Logs
        elif choice == "31":
            run_command("tail -100 logs/sophia.log | less", "Viewing last 100 log lines")
        elif choice == "32":
            run_command("grep -i error logs/sophia.log | tail -50", "Viewing last 50 errors")
        elif choice == "33":
            run_command("sqlite3 .data/tasks.sqlite 'SELECT * FROM tasks ORDER BY created_at DESC LIMIT 20'", "Last 20 tasks")
        elif choice == "34":
            run_command("htop", "System resource monitor")
        elif choice == "35":
            run_command("ls -lh .data/*.db && sqlite3 .data/memory.db '.tables'", "Database status")
        
        # Development Tools
        elif choice == "41":
            run_command("xdg-open http://127.0.0.1:8000/dashboard 2>/dev/null || open http://127.0.0.1:8000/dashboard 2>/dev/null", "Opening Dashboard")
        elif choice == "42":
            run_command(".venv/bin/python capture_dashboard_screenshots.py", "Generating screenshots")
        elif choice == "43":
            run_command("cp -r .data .data_backup_$(date +%Y%m%d_%H%M%S)", "Creating database backup")
        elif choice == "44":
            run_command("sqlite3 .data/tasks.sqlite 'DELETE FROM tasks WHERE status=\"pending\"'", "Clearing pending tasks")
        elif choice == "45":
            run_command("sqlite3 .data/memory.db 'DELETE FROM hypotheses'", "Resetting self-improvement")
        elif choice == "46":
            run_command(".venv/bin/ruff check . --fix", "Running ruff linter")
        
        # Ollama Management
        elif choice == "51":
            run_command("curl -s http://localhost:11434/api/tags | python3 -m json.tool", "Listing Ollama models")
        elif choice == "52":
            model = input("Enter model name (e.g., llama3.1:8b): ").strip()
            if model:
                run_command(f"ollama pull {model}", f"Pulling {model}")
        elif choice == "53":
            run_command("curl -X POST http://localhost:11434/api/generate -d '{\"model\": \"llama3.1:8b\", \"prompt\": \"Hello, test\", \"stream\": false}' | python3 -m json.tool", "Testing llama3.1:8b")
        elif choice == "54":
            run_command("curl -X POST http://localhost:11434/api/generate -d '{\"model\": \"qwen2.5:14b\", \"prompt\": \"Hello, test\", \"stream\": false}' | python3 -m json.tool", "Testing qwen2.5:14b")
        elif choice == "55":
            run_command("systemctl status ollama", "Ollama service status")
        
        # Dashboard Tools
        elif choice == "61":
            run_command("xdg-open http://127.0.0.1:8000/dashboard 2>/dev/null || echo 'Open http://127.0.0.1:8000/dashboard in browser'", "Opening Dashboard")
        elif choice == "62":
            run_command("for endpoint in stats logs tasks hypotheses budget self_improvement; do echo \"\\n=== /api/$endpoint ===\"; curl -s http://127.0.0.1:8000/api/$endpoint | python3 -m json.tool | head -20; done", "Testing all API endpoints")
        elif choice == "63":
            msg = input("Enter test message: ").strip() or "Jaké jsou tvé schopnosti?"
            run_command(f".venv/bin/python -c \"import asyncio; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); page = browser.new_page(); page.goto('http://127.0.0.1:8000/dashboard'); page.click('button:has-text(\\\"Chat\\\")'); page.fill('#chatInput', '{msg}'); page.click('#sendButton'); import time; time.sleep(5); browser.close()\"", "Sending test message")
        elif choice == "64":
            run_command("curl -s http://127.0.0.1:8000/api/stats > dashboard_export_$(date +%Y%m%d_%H%M%S).json && echo 'Exported to dashboard_export_*.json'", "Exporting Dashboard data")
        
        # Advanced
        elif choice == "71":
            run_command(".venv/bin/python -i -c 'import sys; sys.path.insert(0, \".\"); from core.kernel import Kernel; print(\"SOPHIA context loaded. Use Kernel class.\")'", "Python shell with SOPHIA")
        elif choice == "72":
            run_command("sqlite3 .data/memory.db", "Opening database shell")
        elif choice == "73":
            run_command("git status && git diff --stat", "Git status")
        elif choice == "74":
            backup_name = f"sophia_backup_{subprocess.check_output('date +%Y%m%d_%H%M%S', shell=True).decode().strip()}.tar.gz"
            run_command(f"tar -czf /tmp/{backup_name} --exclude='.venv' --exclude='__pycache__' --exclude='.git' .", f"Creating backup: {backup_name}")
        elif choice == "75":
            run_command("echo '=== Disk Usage ===' && df -h . && echo '\\n=== Memory ===' && free -h && echo '\\n=== Python Version ===' && python3 --version && echo '\\n=== Ollama Status ===' && curl -s http://localhost:11434/api/tags | python3 -m json.tool | head -10", "System diagnostics")
        
        elif choice == "0":
            print(f"\n{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}\n")
            sys.exit(0)
        
        else:
            print(f"{Colors.FAIL}Invalid option. Press Enter to continue...{Colors.ENDC}")
            input()

if __name__ == "__main__":
    try:
        # Check if running in correct directory
        if not Path("run.py").exists():
            print(f"{Colors.FAIL}Error: Must run from SOPHIA root directory{Colors.ENDC}")
            sys.exit(1)
        
        main_menu()
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        sys.exit(1)
