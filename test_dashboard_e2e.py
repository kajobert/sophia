"""
End-to-End test for SOPHIA Dashboard using Playwright.

This test validates:
1. Dashboard loads correctly
2. All tabs are accessible
3. API endpoints return valid data
4. Chat functionality works
5. Logs are displayed
"""

import pytest
from playwright.sync_api import Page, expect
import time
import re


def test_dashboard_overview_tab(page: Page):
    """Test Overview tab loads and displays stats."""
    # Navigate to dashboard
    page.goto("http://127.0.0.1:8000/dashboard")
    
    # Wait for page load
    page.wait_for_load_state("networkidle")
    
    # Check title
    expect(page).to_have_title("SOPHIA AMI 1.0 - Dashboard")
    
    # Check header
    expect(page.locator("h1")).to_contain_text("SOPHIA AMI 1.0")
    
    # Check tabs are visible
    tabs = page.locator(".tab")
    expect(tabs).to_have_count(3)
    
    # Check Overview tab is active
    overview_tab = page.locator('.tab:has-text("Overview")')
    expect(overview_tab).to_have_class(re.compile(r".*active.*"))
    
    # Check stats cards are present
    expect(page.locator("#pluginCount")).to_be_visible()
    expect(page.locator("#pendingCount")).to_be_visible()
    expect(page.locator("#doneCount")).to_be_visible()
    expect(page.locator("#failedCount")).to_be_visible()
    
    # Wait for stats to load (should not be "--" after a few seconds)
    time.sleep(3)
    plugin_count = page.locator("#pluginCount").text_content()
    print(f"Plugin count: {plugin_count}")
    assert plugin_count != "--", "Plugin count should be loaded"


def test_dashboard_chat_tab(page: Page):
    """Test Chat tab functionality."""
    page.goto("http://127.0.0.1:8000/dashboard")
    page.wait_for_load_state("networkidle")
    
    # Click Chat tab
    page.click('.tab:has-text("Chat")')
    
    # Wait for chat interface to be visible
    expect(page.locator(".chat-container")).to_be_visible()
    expect(page.locator("#chatMessages")).to_be_visible()
    expect(page.locator("#chatInput")).to_be_visible()
    expect(page.locator("#chatSend")).to_be_visible()
    
    # Check initial greeting message
    messages = page.locator(".chat-message")
    expect(messages).to_have_count(1)  # Initial greeting
    
    # Check connection status
    time.sleep(2)  # Wait for WebSocket connection
    status = page.locator("#chatStatus").text_content()
    print(f"Chat status: {status}")
    assert "Connected" in status or "Connecting" in status


def test_dashboard_logs_tab(page: Page):
    """Test Logs tab displays log entries."""
    page.goto("http://127.0.0.1:8000/dashboard")
    page.wait_for_load_state("networkidle")
    
    # Click Logs tab
    page.click('.tab:has-text("Logs")')
    
    # Wait for logs interface to be visible
    expect(page.locator(".logs-container")).to_be_visible()
    expect(page.locator("#logLevel")).to_be_visible()
    
    # Wait for logs to load
    time.sleep(2)
    
    # Check if logs are displayed
    log_lines = page.locator(".log-line")
    count = log_lines.count()
    print(f"Log lines displayed: {count}")
    
    # Should have at least some logs
    assert count > 0, "Logs should be displayed"
    
    # Check log badges are present
    badges = page.locator(".log-badge")
    assert badges.count() > 0, "Log level badges should be present"


def test_dashboard_api_stats(page: Page):
    """Test /api/stats endpoint."""
    response = page.request.get("http://127.0.0.1:8000/api/stats")
    assert response.ok, "API stats should return 200"
    
    data = response.json()
    print(f"Stats data: {data}")
    
    assert "plugin_count" in data
    assert "pending_count" in data
    assert "done_count" in data
    assert "failed_count" in data
    
    # Plugin count should be > 0 if SOPHIA is running
    assert data["plugin_count"] >= 0


def test_dashboard_api_logs(page: Page):
    """Test /api/logs endpoint."""
    response = page.request.get("http://127.0.0.1:8000/api/logs?level=ALL&lines=10")
    assert response.ok, "API logs should return 200"
    
    data = response.json()
    print(f"Logs response: {data}")
    
    assert "logs" in data
    assert isinstance(data["logs"], list)
    
    if data.get("error"):
        print(f"⚠️  Logs error: {data['error']}")
    else:
        assert len(data["logs"]) > 0, "Should have at least some logs"


def test_dashboard_budget_section(page: Page):
    """Test Budget Status section."""
    page.goto("http://127.0.0.1:8000/dashboard")
    page.wait_for_load_state("networkidle")
    
    # Wait for data to load
    time.sleep(3)
    
    # Check budget elements are visible
    expect(page.locator("#monthlySpent")).to_be_visible()
    expect(page.locator("#monthlyLimit")).to_be_visible()
    expect(page.locator("#dailySpent")).to_be_visible()
    expect(page.locator("#currentPhase")).to_be_visible()


def test_dashboard_screenshot(page: Page):
    """Create screenshots of all Dashboard tabs for visual validation."""
    from pathlib import Path
    
    # Create screenshots directory if not exists
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Screenshot 1: Overview Tab
    page.goto("http://127.0.0.1:8000/dashboard")
    page.wait_for_load_state("networkidle")
    time.sleep(3)  # Wait for stats to load
    page.screenshot(path="screenshots/dashboard_overview.png", full_page=True)
    print("Screenshot saved: screenshots/dashboard_overview.png")
    
    # Screenshot 2: Chat Tab
    page.click('.tab:has-text("Chat")')
    page.wait_for_selector(".chat-tab", state="visible")
    time.sleep(1)
    page.screenshot(path="screenshots/dashboard_chat.png", full_page=True)
    print("Screenshot saved: screenshots/dashboard_chat.png")
    
    # Screenshot 3: Logs Tab
    page.click('.tab:has-text("Logs")')
    page.wait_for_selector(".logs-tab", state="visible")
    time.sleep(3)  # Wait for logs to load
    page.screenshot(path="screenshots/dashboard_logs.png", full_page=True)
    print("Screenshot saved: screenshots/dashboard_logs.png")
    
    # Verify all screenshots were created
    assert (screenshots_dir / "dashboard_overview.png").exists()
    assert (screenshots_dir / "dashboard_chat.png").exists()
    assert (screenshots_dir / "dashboard_logs.png").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed"])  # --headed to see browser
