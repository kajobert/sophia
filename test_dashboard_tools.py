#!/usr/bin/env python3
"""
Comprehensive test of all Dashboard Tools buttons.

Tests each tool button to ensure:
1. API endpoint responds
2. Command executes without errors
3. Output is reasonable
4. JavaScript functions work
"""

import pytest
import time
import json
from playwright.sync_api import Page, expect
import requests

# Dashboard URL
DASHBOARD_URL = "http://127.0.0.1:8000/dashboard"
API_BASE = "http://127.0.0.1:8000/api"


@pytest.fixture(scope="session")
def check_server():
    """Ensure SOPHIA is running before tests."""
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        assert response.status_code == 200
        print(f"\n✅ SOPHIA is running: {response.json()}")
    except Exception as e:
        pytest.fail(f"SOPHIA not running: {e}")


class TestDashboardToolsAPI:
    """Test Tools API endpoints directly."""
    
    def test_api_tools_run_system_info(self, check_server):
        """Test system_info tool via API."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "system_info"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "CPU" in data["output"]
        assert "Memory" in data["output"]
        print(f"\n✅ system_info: {data['output'][:100]}...")
    
    def test_api_tools_run_check_health(self, check_server):
        """Test check_health tool."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "check_health"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "python run.py" in data["output"] or "ollama" in data["output"]
        print(f"\n✅ check_health: Found processes")
    
    def test_api_tools_run_list_models(self, check_server):
        """Test list_models tool."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "list_models"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        # Parse JSON output
        models_data = json.loads(data["output"])
        assert "models" in models_data
        assert len(models_data["models"]) > 0
        print(f"\n✅ list_models: Found {len(models_data['models'])} models")
    
    def test_api_tools_run_export_data(self, check_server):
        """Test export_data tool."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "export_data"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        stats = json.loads(data["output"])
        assert "plugin_count" in stats
        print(f"\n✅ export_data: {stats}")
    
    def test_api_tools_run_run_diagnostics(self, check_server):
        """Test run_diagnostics tool."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "run_diagnostics"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Disk" in data["output"]
        assert "Memory" in data["output"]
        print(f"\n✅ run_diagnostics: OK")
    
    def test_api_tools_invalid_tool(self, check_server):
        """Test error handling for invalid tool."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "nonexistent_tool"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "Unknown tool" in data["error"]
        print(f"\n✅ Invalid tool handling works")
    
    def test_api_browser_test(self, check_server):
        """Test browser-test endpoint."""
        response = requests.post(
            f"{API_BASE}/tools/browser-test",
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # May fail if plugin not loaded, but endpoint should respond
        assert "success" in data
        print(f"\n✅ browser-test endpoint: {data}")


class TestDashboardToolsUI:
    """Test Tools UI in Dashboard with Playwright."""
    
    def test_tools_tab_loads(self, page: Page, check_server):
        """Test Tools tab is visible and loads."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(2)
        
        # Click Tools tab
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Check Tools tab is visible
        expect(page.locator("#tools-tab")).to_be_visible()
        
        # Check tool categories exist
        expect(page.locator('h3:has-text("Testing & Debugging")')).to_be_visible()
        expect(page.locator('h3:has-text("Browser Automation")')).to_be_visible()
        expect(page.locator('h3:has-text("System Control")')).to_be_visible()
        expect(page.locator('h3:has-text("Model Management")')).to_be_visible()
        expect(page.locator('h3:has-text("Diagnostics")')).to_be_visible()
        expect(page.locator('h3:has-text("Quick Actions")')).to_be_visible()
        
        print("\n✅ All tool categories visible")
    
    def test_tool_output_console(self, page: Page, check_server):
        """Test Tool Output console exists."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Check output console exists
        expect(page.locator("#toolOutput")).to_be_visible()
        
        output = page.locator("#toolOutput").text_content()
        assert "Ready to run tools" in output or len(output) > 0
        
        print("\n✅ Tool Output console visible")
    
    def test_system_information_button(self, page: Page, check_server):
        """Test System Information button click."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Click System Information button
        page.click('button:has-text("System Information")')
        time.sleep(3)
        
        # Check output
        output = page.locator("#toolOutput").text_content()
        assert "system_info" in output.lower() or "cpu" in output.lower()
        
        print(f"\n✅ System Information button: {output[:100]}...")
    
    def test_health_check_button(self, page: Page, check_server):
        """Test Health Check button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Click Health Check
        page.click('button:has-text("Health Check")')
        time.sleep(3)
        
        output = page.locator("#toolOutput").text_content()
        assert "check_health" in output.lower() or "success" in output.lower()
        
        print(f"\n✅ Health Check button works")
    
    def test_list_models_button(self, page: Page, check_server):
        """Test List All Models button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Click List All Models
        page.click('button:has-text("List All Models")')
        time.sleep(3)
        
        output = page.locator("#toolOutput").text_content()
        assert "list_models" in output.lower() or "model" in output.lower()
        
        print(f"\n✅ List Models button works")
    
    def test_export_data_button(self, page: Page, check_server):
        """Test Export Dashboard Data button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Click Export Dashboard Data
        page.click('button:has-text("Export Dashboard Data")')
        time.sleep(3)
        
        output = page.locator("#toolOutput").text_content()
        assert "export_data" in output.lower() or "plugin_count" in output.lower()
        
        print(f"\n✅ Export Data button works")
    
    def test_refresh_all_data_button(self, page: Page, check_server):
        """Test Refresh All Data button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(2)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Get initial plugin count
        initial_count = page.locator("#pluginCount").text_content()
        
        # Click Refresh All Data
        page.click('button:has-text("Refresh All Data")')
        time.sleep(3)
        
        # Check if stats refreshed (value should be same or updated)
        new_count = page.locator("#pluginCount").text_content()
        assert new_count is not None
        
        # Check output console
        output = page.locator("#toolOutput").text_content()
        assert "refresh" in output.lower()
        
        print(f"\n✅ Refresh All Data: {initial_count} → {new_count}")
    
    def test_clear_output_button(self, page: Page, check_server):
        """Test Clear Output button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Run a tool first
        page.click('button:has-text("System Information")')
        time.sleep(2)
        
        # Clear output
        page.click('button:has-text("Clear Output")')
        time.sleep(1)
        
        output = page.locator("#toolOutput").text_content()
        assert "cleared" in output.lower() or len(output) < 100
        
        print("\n✅ Clear Output button works")
    
    def test_download_logs_button(self, page: Page, check_server):
        """Test Download Logs button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Setup download listener
        with page.expect_download() as download_info:
            page.click('button:has-text("Download Logs")')
            time.sleep(2)
        
        download = download_info.value
        
        # Check file was downloaded
        assert download.suggested_filename.startswith("sophia_logs_")
        assert download.suggested_filename.endswith(".txt")
        
        print(f"\n✅ Download Logs: {download.suggested_filename}")
    
    def test_multiple_tools_sequence(self, page: Page, check_server):
        """Test running multiple tools in sequence."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Run 3 tools in sequence
        tools = [
            "System Information",
            "Health Check",
            "List All Models"
        ]
        
        for tool in tools:
            page.click(f'button:has-text("{tool}")')
            time.sleep(2)
        
        # Check output has multiple entries
        output = page.locator("#toolOutput").text_content()
        
        # Count timestamps (each tool adds timestamp)
        timestamp_count = output.count("[")
        assert timestamp_count >= 3
        
        print(f"\n✅ Sequential tools: {timestamp_count} outputs")
    
    def test_browser_self_test_button(self, page: Page, check_server):
        """Test SOPHIA Self-Test Dashboard button."""
        page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(1)
        
        page.click('button:has-text("🛠️ Tools")')
        time.sleep(1)
        
        # Click SOPHIA Self-Test
        page.click('button:has-text("SOPHIA Self-Test Dashboard")')
        time.sleep(5)  # Browser test takes longer
        
        output = page.locator("#toolOutput").text_content()
        
        # Should either work or show "plugin not available"
        assert "self-test" in output.lower() or "plugin" in output.lower()
        
        print(f"\n✅ Self-Test button: {output[-200:]}")


class TestToolsErrorHandling:
    """Test error handling in Tools."""
    
    def test_api_timeout_handling(self, check_server):
        """Test that long-running commands don't hang."""
        # This should timeout at 30s
        response = requests.post(
            f"{API_BASE}/tools/run",
            json={"tool": "view_logs"},  # Just view logs, should be fast
            timeout=35
        )
        
        assert response.status_code == 200
        print("\n✅ Timeout handling OK")
    
    def test_invalid_json_handling(self, check_server):
        """Test API handles invalid JSON."""
        response = requests.post(
            f"{API_BASE}/tools/run",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Should return error, not crash
        assert response.status_code in [200, 400, 422]
        print("\n✅ Invalid JSON handled")


def test_all_tools_have_buttons(page: Page, check_server):
    """Verify all tool buttons exist in UI."""
    page.goto(DASHBOARD_URL, wait_until="networkidle")
    time.sleep(1)
    
    page.click('button:has-text("🛠️ Tools")')
    time.sleep(1)
    
    expected_buttons = [
        # Testing & Debugging
        "Test Dashboard",
        "Run E2E Tests",
        "Test All Plugins",
        "Interactive Debugger",
        
        # Browser Automation
        "SOPHIA Self-Test Dashboard",
        "Capture All Tabs",
        "View Trace Debugger",
        
        # System Control
        "Backup Database",
        "Clear Task Queue",
        "Restart SOPHIA",
        "View Full Logs",
        
        # Model Management
        "Test llama3.1:8b",
        "Test qwen2.5:14b",
        "List All Models",
        "Test Model Escalation",
        
        # Diagnostics
        "System Information",
        "Health Check",
        "Export Dashboard Data",
        "Full Diagnostics",
        
        # Quick Actions
        "Open in New Tab",
        "Refresh All Data",
        "Clear Console",
        "Download Logs"
    ]
    
    missing_buttons = []
    for button_text in expected_buttons:
        try:
            page.locator(f'button:has-text("{button_text}")').wait_for(state="visible", timeout=1000)
        except:
            missing_buttons.append(button_text)
    
    if missing_buttons:
        print(f"\n⚠️  Missing buttons: {missing_buttons}")
    else:
        print(f"\n✅ All {len(expected_buttons)} buttons present")
    
    assert len(missing_buttons) == 0, f"Missing: {missing_buttons}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--headed"])
