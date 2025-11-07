#!/usr/bin/env python3
"""Manual Dashboard debugging tool with hooks and interactive controls.

Usage:
    # Test specific scenario
    python dashboard_debug.py --scenario chat
    
    # Interactive mode with pauses
    python dashboard_debug.py --interactive
    
    # Test WebSocket with monitoring
    python dashboard_debug.py --monitor-ws
"""

from playwright.sync_api import sync_playwright, Page
from pathlib import Path
import time
import json

class DashboardDebugger:
    """Interactive Dashboard debugger with hooks and screenshots."""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.screenshots_dir = Path("screenshots/debug")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_counter = 0
        self.console_logs = []
        self.network_logs = []
        self.ws_messages = []
        
    def setup_hooks(self, page: Page):
        """Setup all monitoring hooks."""
        print("🔗 Setting up monitoring hooks...")
        
        # Console messages
        def on_console(msg):
            entry = f"[{msg.type.upper()}] {msg.text}"
            self.console_logs.append(entry)
            if msg.type in ['error', 'warning']:
                print(f"   🚨 {entry}")
        
        page.on("console", on_console)
        
        # Page errors
        def on_error(exc):
            error = f"PAGE ERROR: {exc}"
            self.console_logs.append(error)
            print(f"   ❌ {error}")
        
        page.on("pageerror", on_error)
        
        # Network requests
        def on_request(request):
            if '/api/' in request.url:
                self.network_logs.append(f"→ {request.method} {request.url}")
                print(f"   📡 API Request: {request.method} {request.url}")
        
        def on_response(response):
            if '/api/' in response.url:
                status = "✅" if response.ok else "❌"
                self.network_logs.append(f"← {response.status} {response.url}")
                print(f"   {status} API Response: {response.status} {response.url}")
        
        page.on("request", on_request)
        page.on("response", on_response)
        
        # WebSocket monitoring
        def on_websocket(ws):
            print(f"   🔌 WebSocket connected: {ws.url}")
            
            def on_frame_sent(payload):
                self.ws_messages.append({"direction": "SEND", "data": payload})
                print(f"   ⬆️  WS SEND: {payload[:100]}...")
            
            def on_frame_received(payload):
                self.ws_messages.append({"direction": "RECV", "data": payload})
                print(f"   ⬇️  WS RECV: {payload[:100]}...")
            
            ws.on("framesent", on_frame_sent)
            ws.on("framereceived", on_frame_received)
        
        page.on("websocket", on_websocket)
        
        print("   ✅ All hooks configured\n")
    
    def capture(self, page: Page, name: str):
        """Capture screenshot with auto-incrementing counter."""
        self.screenshot_counter += 1
        filename = f"{self.screenshot_counter:02d}_{name}.png"
        path = self.screenshots_dir / filename
        page.screenshot(path=path)
        print(f"   📸 Screenshot: {filename}")
        return path
    
    def inspect_element(self, page: Page, selector: str):
        """Inspect element properties."""
        print(f"\n🔍 Inspecting: {selector}")
        
        try:
            element = page.locator(selector)
            
            # Check visibility
            visible = element.is_visible()
            print(f"   Visible: {visible}")
            
            if visible:
                # Get properties
                text = element.text_content()
                print(f"   Text: {text[:100]}...")
                
                # Get attributes
                classes = element.get_attribute("class")
                print(f"   Classes: {classes}")
                
                # Bounding box
                bbox = element.bounding_box()
                if bbox:
                    print(f"   Position: x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def wait_for_user(self, prompt="Press Enter to continue..."):
        """Pause and wait for user input."""
        if not self.headless:
            input(f"\n⏸️  {prompt}\n")
    
    def test_overview_tab(self, page: Page):
        """Test Overview tab with detailed inspection."""
        print("\n" + "="*60)
        print("📊 TESTING: Overview Tab")
        print("="*60)
        
        page.goto("http://127.0.0.1:8000/dashboard", wait_until="networkidle")
        time.sleep(2)
        
        self.capture(page, "overview_initial")
        
        # Inspect stats cards
        print("\n🔢 Checking Stats Cards...")
        stats = {
            "Plugins": "#pluginCount",
            "Pending": "#pendingCount",
            "Done": "#doneCount",
            "Failed": "#failedCount"
        }
        
        for name, selector in stats.items():
            value = page.locator(selector).text_content()
            print(f"   {name}: {value}")
        
        # Check hypotheses table
        print("\n📋 Checking Hypotheses Table...")
        rows = page.locator("#hypothesesTable tbody tr")
        count = rows.count()
        print(f"   Rows: {count}")
        
        if count > 0:
            # Inspect first row
            first_row = rows.first
            cells = first_row.locator("td")
            print(f"   First row cells: {cells.count()}")
            for i in range(min(cells.count(), 5)):
                cell_text = cells.nth(i).text_content()
                print(f"     Cell {i}: {cell_text}")
        
        self.capture(page, "overview_inspected")
        self.wait_for_user("Overview tab inspected. Continue to Chat?")
    
    def test_chat_tab(self, page: Page, message="Jaké jsou tvé aktuální schopnosti?"):
        """Test Chat tab with WebSocket monitoring."""
        print("\n" + "="*60)
        print("💬 TESTING: Chat Tab")
        print("="*60)
        
        # Switch to chat
        page.click('button:has-text("💬 Chat")')
        time.sleep(1)
        
        self.capture(page, "chat_tab_opened")
        
        # Inspect chat elements
        print("\n🔍 Inspecting Chat UI...")
        self.inspect_element(page, "#chatMessages")
        self.inspect_element(page, "#chatInput")
        self.inspect_element(page, "#sendButton")
        
        # Type message
        print(f"\n⌨️  Typing message: '{message}'")
        page.fill("#chatInput", message)
        self.capture(page, "chat_message_typed")
        
        self.wait_for_user("Message ready. Press Enter to send...")
        
        # Clear WS messages before sending
        self.ws_messages.clear()
        
        # Send message
        print("📤 Sending message...")
        page.click("#sendButton")
        time.sleep(1)
        
        self.capture(page, "chat_message_sent")
        
        # Wait for response
        print("⏳ Waiting for response (max 60s)...")
        try:
            page.wait_for_selector(
                ".chat-message.assistant",
                timeout=60000,
                state="visible"
            )
            
            time.sleep(2)  # Let it fully render
            
            # Get all messages
            messages = page.locator(".chat-message")
            count = messages.count()
            print(f"\n💬 Total messages in chat: {count}")
            
            # Get last assistant message
            last_assistant = page.locator(".chat-message.assistant .chat-bubble").last
            response = last_assistant.text_content()
            print(f"\n📨 SOPHIA's response:")
            print(f"   {response[:300]}...")
            
            self.capture(page, "chat_response_received")
            
            # Show WebSocket traffic
            print(f"\n🔌 WebSocket messages exchanged: {len(self.ws_messages)}")
            for i, msg in enumerate(self.ws_messages[:5]):
                print(f"   {i+1}. {msg['direction']}: {msg['data'][:80]}...")
            
        except Exception as e:
            print(f"❌ No response: {e}")
            self.capture(page, "chat_no_response")
        
        self.wait_for_user("Chat test complete. Continue to Logs?")
    
    def test_logs_tab(self, page: Page):
        """Test Logs tab with filtering."""
        print("\n" + "="*60)
        print("📋 TESTING: Logs Tab")
        print("="*60)
        
        # Switch to logs
        page.click('button:has-text("📋 Logs")')
        time.sleep(2)
        
        self.capture(page, "logs_tab_opened")
        
        # Count initial logs
        log_lines = page.locator("#logContent .log-line")
        initial_count = log_lines.count()
        print(f"\n📊 Total log lines: {initial_count}")
        
        # Test filters
        filters = ["INFO", "WARNING", "ERROR", "DEBUG"]
        for level in filters:
            print(f"\n🔍 Testing filter: {level}")
            page.select_option("#logLevel", level)
            time.sleep(1)
            
            count = log_lines.count()
            print(f"   {level} logs: {count}")
            
            if count > 0:
                # Show first log of this type
                first_log = log_lines.first.text_content()
                print(f"   First: {first_log[:100]}...")
            
            self.capture(page, f"logs_filter_{level.lower()}")
        
        # Reset to ALL
        page.select_option("#logLevel", "ALL")
        time.sleep(1)
        
        self.wait_for_user("Logs test complete.")
    
    def save_debug_report(self):
        """Save comprehensive debug report."""
        report_path = self.screenshots_dir / "debug_report.json"
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_screenshots": self.screenshot_counter,
            "console_logs": self.console_logs,
            "network_requests": self.network_logs,
            "websocket_messages": len(self.ws_messages),
            "screenshots_dir": str(self.screenshots_dir.absolute())
        }
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Debug report saved: {report_path}")
        
        # Also save detailed WS log
        if self.ws_messages:
            ws_log_path = self.screenshots_dir / "websocket_log.json"
            with open(ws_log_path, "w") as f:
                json.dump(self.ws_messages, f, indent=2)
            print(f"📄 WebSocket log saved: {ws_log_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard debugging tool")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--scenario", choices=["overview", "chat", "logs", "all"], 
                       default="all", help="Which scenario to test")
    parser.add_argument("--message", default="Jaké jsou tvé aktuální schopnosti?",
                       help="Message to send in chat test")
    parser.add_argument("--interactive", action="store_true", 
                       help="Pause between steps")
    
    args = parser.parse_args()
    
    debugger = DashboardDebugger(headless=args.headless)
    
    with sync_playwright() as p:
        print("🚀 Starting Dashboard Debugger...")
        
        browser = p.chromium.launch(
            headless=args.headless,
            slow_mo=500 if args.interactive else 0
        )
        
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        # Setup all hooks
        debugger.setup_hooks(page)
        
        try:
            # Run selected scenario
            if args.scenario in ["overview", "all"]:
                debugger.test_overview_tab(page)
            
            if args.scenario in ["chat", "all"]:
                debugger.test_chat_tab(page, message=args.message)
            
            if args.scenario in ["logs", "all"]:
                debugger.test_logs_tab(page)
            
            # Save debug report
            debugger.save_debug_report()
            
            print("\n✨ Debugging complete!")
            print(f"📁 All artifacts saved to: {debugger.screenshots_dir}")
            
            if not args.headless:
                input("\nPress Enter to close browser...")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            debugger.capture(page, "error_state")
            debugger.save_debug_report()
        
        finally:
            browser.close()

if __name__ == "__main__":
    main()
