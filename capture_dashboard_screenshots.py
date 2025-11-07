#!/usr/bin/env python3
"""Simple script to capture Dashboard screenshots using Playwright."""

from playwright.sync_api import sync_playwright
from pathlib import Path
import time

def capture_screenshots():
    """Capture screenshots of all Dashboard tabs."""
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        try:
            # Screenshot 1: Overview Tab
            print("Navigating to Dashboard...")
            page.goto("http://127.0.0.1:8000/dashboard", wait_until="networkidle")
            time.sleep(3)  # Wait for stats to load
            screenshot_path = "screenshots/dashboard_overview.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved: {screenshot_path}")
            
            # Screenshot 2: Chat Tab
            print("Switching to Chat tab...")
            page.click('button:has-text("💬 Chat")')
            page.wait_for_selector("#chat-tab", state="visible")
            time.sleep(1)
            screenshot_path = "screenshots/dashboard_chat.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved: {screenshot_path}")
            
            # Screenshot 3: Logs Tab
            print("Switching to Logs tab...")
            page.click('button:has-text("📋 Logs")')
            page.wait_for_selector("#logs-tab", state="visible")
            time.sleep(3)  # Wait for logs to load
            screenshot_path = "screenshots/dashboard_logs.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved: {screenshot_path}")
            
            print("\n✨ All screenshots captured successfully!")
            print(f"📁 Screenshots saved to: {screenshots_dir.absolute()}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    capture_screenshots()
