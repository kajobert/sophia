#!/usr/bin/env python3
"""Interactive Dashboard testing and debugging with Playwright.

This script allows you to:
1. See the browser in action (--headed mode)
2. Interact with Dashboard manually
3. Capture screenshots at any point
4. See console logs and errors
5. Test WebSocket chat functionality
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import argparse

def test_dashboard_interactive(headless=False, slow_mo=1000):
    """Interactive Dashboard testing with visual feedback."""
    screenshots_dir = Path("screenshots/debug")
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 Starting interactive Dashboard test...")
    print(f"📁 Screenshots will be saved to: {screenshots_dir}")
    print(f"🎬 Browser mode: {'headless' if headless else 'visible'}")
    
    with sync_playwright() as p:
        # Launch browser with slow_mo to see actions
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo  # Slow down by N ms to see actions
        )
        
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="screenshots/debug/videos" if not headless else None
        )
        
        # Enable tracing for debugging
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        
        page = context.new_page()
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        # Capture errors
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        
        try:
            print("\n📊 Step 1: Loading Dashboard Overview...")
            page.goto("http://127.0.0.1:8000/dashboard", wait_until="networkidle")
            time.sleep(2)
            
            # Check stats loaded
            plugin_count = page.locator("#pluginCount").text_content()
            pending_count = page.locator("#pendingCount").text_content()
            print(f"   ✅ Stats loaded: Plugins={plugin_count}, Pending={pending_count}")
            
            page.screenshot(path=screenshots_dir / "01_overview_loaded.png")
            print(f"   📸 Screenshot: 01_overview_loaded.png")
            
            # Check hypotheses table
            hypotheses_rows = page.locator("#hypothesesOverviewBody tr").count()
            print(f"   ✅ Hypotheses table (overview) rows: {hypotheses_rows}")
            
            page.screenshot(path=screenshots_dir / "02_hypotheses_table.png")
            print(f"   📸 Screenshot: 02_hypotheses_table.png")
            
            print("\n💬 Step 2: Testing Chat Tab...")
            page.click('button:has-text("💬 Chat")')
            time.sleep(1)
            
            # Check chat elements
            chat_visible = page.locator("#chat-tab").is_visible()
            print(f"   ✅ Chat tab visible: {chat_visible}")
            
            page.screenshot(path=screenshots_dir / "03_chat_tab_opened.png")
            print(f"   📸 Screenshot: 03_chat_tab_opened.png")
            
            # Test sending a message
            print("\n🔄 Step 3: Sending test message...")
            message_input = page.locator("#chatInput")
            message_input.fill("Jaké jsou tvé aktuální schopnosti?")
            
            page.screenshot(path=screenshots_dir / "04_message_typed.png")
            print(f"   📸 Screenshot: 04_message_typed.png")
            
            # Click send button
            page.click("#chatSend")
            print("   ✅ Message sent via WebSocket")
            
            # Wait for response (up to 30 seconds)
            print("   ⏳ Waiting for SOPHIA's response...")
            try:
                page.wait_for_selector(
                    ".chat-message.assistant",
                    timeout=30000,
                    state="visible"
                )
                print("   ✅ Response received!")
                
                # Get response text
                response = page.locator(".chat-message.assistant .chat-bubble").last.text_content()
                print(f"   💬 Response preview: {response[:200]}...")
                
                page.screenshot(path=screenshots_dir / "05_chat_response.png", full_page=True)
                print(f"   📸 Screenshot: 05_chat_response.png")
                
            except Exception as e:
                print(f"   ⚠️  No response within 30s: {e}")
                page.screenshot(path=screenshots_dir / "05_chat_no_response.png")
            
            print("\n📋 Step 4: Testing Logs Tab...")
            page.click('button:has-text("📋 Logs")')
            time.sleep(2)
            
            # Check logs loaded
            log_lines = page.locator("#logsContainer .log-line").count()
            print(f"   ✅ Log lines displayed: {log_lines}")
            
            # Test log filtering
            page.select_option("#logLevel", "ERROR")
            time.sleep(1)
            error_lines = page.locator("#logsContainer .log-line").count()
            print(f"   ✅ ERROR filter: {error_lines} lines")
            
            page.screenshot(path=screenshots_dir / "06_logs_tab.png", full_page=True)
            print(f"   📸 Screenshot: 06_logs_tab.png")
            
            # Reset to ALL
            page.select_option("#logLevel", "ALL")
            time.sleep(1)
            
            print("\n📊 Step 5: Back to Overview - checking auto-refresh...")
            page.click('button:has-text("📊 Overview")')
            time.sleep(1)
            
            # Check if stats auto-refresh works
            old_pending = pending_count
            time.sleep(6)  # Wait for auto-refresh (every 5s)
            new_pending = page.locator("#pendingCount").text_content()
            print(f"   📈 Stats after 6s: Pending {old_pending} → {new_pending}")
            
            page.screenshot(path=screenshots_dir / "07_overview_refreshed.png")
            print(f"   📸 Screenshot: 07_overview_refreshed.png")
            
            # Final full-page screenshot
            page.screenshot(path=screenshots_dir / "08_final_state.png", full_page=True)
            print(f"   📸 Screenshot: 08_final_state.png")
            
            print("\n📝 Console Messages:")
            for msg in console_messages[-10:]:  # Last 10 messages
                print(f"   {msg}")
            
            if errors:
                print("\n❌ JavaScript Errors:")
                for err in errors:
                    print(f"   {err}")
            else:
                print("\n✅ No JavaScript errors detected")
            
            print("\n✨ Test complete! Press Enter to close browser...")
            if not headless:
                input()  # Wait for user to inspect
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path=screenshots_dir / "error_state.png", full_page=True)
            print(f"📸 Error screenshot: error_state.png")
            
        finally:
            # Save trace for detailed debugging
            context.tracing.stop(path=screenshots_dir / "trace.zip")
            print(f"\n🔍 Trace saved: {screenshots_dir / 'trace.zip'}")
            print("   View with: playwright show-trace screenshots/debug/trace.zip")
            
            context.close()
            browser.close()

def test_chat_websocket_only():
    """Quick test focused on WebSocket chat functionality."""
    print("🔌 Testing WebSocket Chat...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        # Monitor WebSocket connections
        ws_messages = []
        
        def on_websocket(ws):
            print(f"   ✅ WebSocket connected: {ws.url}")
            ws.on("framereceived", lambda payload: ws_messages.append(f"RECV: {payload}"))
            ws.on("framesent", lambda payload: ws_messages.append(f"SEND: {payload}"))
        
        page.on("websocket", on_websocket)
        
        try:
            page.goto("http://127.0.0.1:8000/dashboard")
            page.click('button:has-text("💬 Chat")')
            time.sleep(2)
            
            # Send message
            page.fill("#chatInput", "Test WebSocket connection")
            page.click("#chatSend")
            
            print("\n📨 WebSocket Messages:")
            time.sleep(5)
            for msg in ws_messages:
                print(f"   {msg}")
            
            print("\n✅ WebSocket test complete. Press Enter to close...")
            input()
            
        finally:
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive Dashboard testing")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--slow", type=int, default=1000, help="Slow down actions by N ms (default: 1000)")
    parser.add_argument("--ws-only", action="store_true", help="Test WebSocket only")
    
    args = parser.parse_args()
    
    if args.ws_only:
        test_chat_websocket_only()
    else:
        test_dashboard_interactive(headless=args.headless, slow_mo=args.slow)
