"""
Dashboard E2E Tests

Comprehensive Playwright tests for Sophia dashboard:
- Overview tab (stats, tasks table)
- Hypotheses tab
- Tools tab (button functionality)
- Logs tab
- Benchmarks tab (new)
- Data loading and error handling
- Navigation and interactions

Run:
    # Headless (CI mode)
    pytest tests/e2e/test_dashboard.py
    
    # Headed (see browser)
    pytest tests/e2e/test_dashboard.py --headed
    
    # Specific test
    pytest tests/e2e/test_dashboard.py::test_overview_tab_loads -v
    
    # With screenshots on failure
    pytest tests/e2e/test_dashboard.py --screenshot=on
"""

import re
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.dashboard
class TestDashboardOverview:
    """Test dashboard Overview tab."""

    def test_page_loads_successfully(self, page: Page):
        """Verify dashboard page loads without errors."""
        # Check title
        expect(page).to_have_title("SOPHIA AMI 1.0 - Dashboard")
        
        # Check header
        header = page.locator("h1")
        expect(header).to_contain_text("SOPHIA AMI 1.0")

    def test_tabs_are_visible(self, page: Page):
        """Verify all tabs are rendered."""
        tabs = ["Overview", "Hypotheses", "Tools", "Logs", "Chat", "Benchmarks"]
        
        for tab_name in tabs:
            tab = page.locator(f"button.tab:has-text('{tab_name}')")
            expect(tab).to_be_visible()

    def test_overview_tab_active_by_default(self, page: Page):
        """Verify Overview tab is active on page load."""
        overview_tab = page.locator("button.tab:has-text('Overview')")
        expect(overview_tab).to_have_class(re.compile(".*active.*"))
        
        overview_content = page.locator("#overview-tab")
        expect(overview_content).to_have_class(re.compile(".*active.*"))

    def test_stats_cards_displayed(self, page: Page):
        """Verify statistics cards are visible."""
        # Should have plugin count, pending, done, failed cards
        stat_cards = page.locator(".card .stat")
        expect(stat_cards).to_have_count(4, timeout=10000)

    def test_tasks_table_loads(self, page: Page, take_screenshot):
        """Verify tasks table loads data or shows empty state."""
        # Wait for API call to complete
        page.wait_for_timeout(2000)
        
        table_body = page.locator("#taskTableBody")
        expect(table_body).to_be_visible()
        
        # Check if table has data or empty message
        rows = table_body.locator("tr")
        row_count = rows.count()
		
        if row_count == 1:
            # Empty or error state row
            first_cell = rows.first.locator("td")
            text_content = first_cell.text_content()
            if text_content and "Error" in text_content:
                expect(first_cell).to_contain_text("Error")
            else:
                expect(first_cell).to_contain_text("No tasks in queue")
        else:
            # Has tasks - verify structure
            first_row = rows.first
            expect(first_row.locator("td").nth(0)).to_be_visible()  # Task ID
            expect(first_row.locator("td").nth(1)).to_be_visible()  # Status
        
        take_screenshot("tasks_table")

    def test_auto_refresh_works(self, page: Page):
        """Verify auto-refresh updates timestamp."""
        # Get initial timestamp from overview panel only
        timestamp_before = page.locator("#lastUpdate").text_content()
		
        # Trigger an immediate refresh to avoid long sleeps and wait for DOM to update
        page.evaluate("refreshDashboard()")
        page.wait_for_function(
            "initial => document.getElementById('lastUpdate').textContent !== initial",
            arg=timestamp_before,
            timeout=10000,
        )
		
        # Check timestamp changed
        timestamp_after = page.locator("#lastUpdate").text_content()
        assert timestamp_before != timestamp_after, "Auto-refresh should update timestamp"


@pytest.mark.e2e
@pytest.mark.dashboard
class TestDashboardHypotheses:
    """Test Hypotheses tab functionality."""

    def test_hypotheses_tab_navigation(self, page: Page):
        """Verify clicking Hypotheses tab switches content."""
        # Click Hypotheses tab
        hyp_tab = page.locator("button.tab:has-text('Hypotheses')")
        hyp_tab.click()
        
        # Wait for tab transition
        page.wait_for_timeout(500)
        
        # Check tab is active
        expect(hyp_tab).to_have_class(re.compile(".*active.*"))
        
        # Check content is visible
        hyp_content = page.locator("#hypotheses-tab")
        expect(hyp_content).to_have_class(re.compile(".*active.*"))

    def test_hypotheses_table_loads(self, page: Page, take_screenshot):
        """Verify hypotheses table loads data."""
        # Navigate to Hypotheses tab
        page.locator("button.tab:has-text('Hypotheses')").click()
        page.wait_for_timeout(2000)  # Wait for API call
        
        table_body = page.locator("#hypotheses-tab #hypothesesDetailBody")
        expect(table_body).to_be_visible()
        
        # Check for data or empty state
        rows = table_body.locator("tr")
        count = rows.count()
        
        if count == 1:
            # Empty or error state
            empty_msg = rows.first.locator("td")
            text_content = empty_msg.text_content()
            if text_content and "Error" in text_content:
                expect(empty_msg).to_contain_text("Error")
            else:
                expect(empty_msg).to_contain_text("No hypotheses")
        else:
            # Has hypotheses - verify columns
            first_row = rows.first
            expect(first_row.locator("td").nth(0)).to_be_visible()  # ID
            expect(first_row.locator("td").nth(1)).to_be_visible()  # Description
            expect(first_row.locator("td").nth(2)).to_be_visible()  # Category
            expect(first_row.locator("td").nth(3)).to_be_visible()  # Status
        
        take_screenshot("hypotheses_table")

    def test_hypotheses_status_badges(self, page: Page):
        """Verify hypothesis status badges are rendered correctly."""
        page.locator("button.tab:has-text('Hypotheses')").click()
        page.wait_for_timeout(2000)
        
        # Look for status badges (if hypotheses exist)
        table_body = page.locator("#hypotheses-tab #hypothesesDetailBody")
        rows = table_body.locator("tr")
        row_count = rows.count()
        
        if row_count > 1:  # Has data
            # Status should have emoji indicator
            status_cell = rows.first.locator("td").nth(3)
            status_text = status_cell.text_content()
            
            # Should contain emoji
            assert any(emoji in status_text for emoji in ["✅", "⚠️", "🔄", "👍", "🧪", "⏳"])


@pytest.mark.e2e
@pytest.mark.dashboard
class TestDashboardTools:
    """Test Tools tab and button functionality."""

    def test_tools_tab_navigation(self, page: Page):
        """Verify Tools tab navigation works."""
        tools_tab = page.locator("button.tab:has-text('Tools')")
        tools_tab.click()
        
        page.wait_for_timeout(500)
        
        expect(tools_tab).to_have_class(re.compile(".*active.*"))
        
        tools_content = page.locator("#tools-tab")
        expect(tools_content).to_have_class(re.compile(".*active.*"))

    def test_tool_buttons_visible(self, page: Page, take_screenshot):
        """Verify all tool buttons are rendered."""
        page.locator("button.tab:has-text('Tools')").click()
        page.wait_for_timeout(500)
        
        # Check for tool buttons grid
        tool_buttons = page.locator(".tool-button")
        count = tool_buttons.count()
        
        assert count > 0, "Should have at least one tool button"
        
        take_screenshot("tools_tab")

    def test_run_test_button_works(self, page: Page):
        """Verify 'Run Test' button triggers action."""
        page.locator("button.tab:has-text('Tools')").click()
        page.wait_for_timeout(500)
        
        # Find Run Test button
        run_test_btn = page.locator(".tool-button:has-text('Run Test')")
        
        if run_test_btn.count() > 0:
            run_test_btn.click()
            
            # Wait for response (success or error message)
            page.wait_for_timeout(3000)
            
            # Check for success/error message
            success_msg = page.locator(".success-msg")
            error_msg = page.locator(".error-msg")
            
            # One of them should be visible
            assert success_msg.is_visible() or error_msg.is_visible(), \
                "Should show success or error message after tool execution"

    def test_browser_test_button_works(self, page: Page):
        """Verify 'Browser Test' button works."""
        page.locator("button.tab:has-text('Tools')").click()
        page.wait_for_timeout(500)
        
        browser_test_btn = page.locator(".tool-button:has-text('Browser Test')")
        
        if browser_test_btn.count() > 0:
            browser_test_btn.click()
            
            page.wait_for_timeout(3000)
            
            # Check for response
            success_msg = page.locator(".success-msg")
            error_msg = page.locator(".error-msg")
            
            assert success_msg.is_visible() or error_msg.is_visible()


@pytest.mark.e2e
@pytest.mark.dashboard
class TestDashboardLogs:
    """Test Logs tab functionality."""

    def test_logs_tab_loads(self, page: Page):
        """Verify Logs tab loads successfully."""
        logs_tab = page.locator("button.tab:has-text('Logs')")
        logs_tab.click()
        
        page.wait_for_timeout(2000)  # Wait for API call
        
        expect(logs_tab).to_have_class(re.compile(".*active.*"))
        
        logs_content = page.locator("#logs-tab")
        expect(logs_content).to_have_class(re.compile(".*active.*"))

    def test_logs_container_visible(self, page: Page, take_screenshot):
        """Verify logs container renders."""
        page.locator("button.tab:has-text('Logs')").click()
        page.wait_for_timeout(2000)
        
        logs_container = page.locator(".logs-container")
        expect(logs_container).to_be_visible()
        
        take_screenshot("logs_tab")

    def test_log_level_filter(self, page: Page):
        """Verify log level filter dropdown exists."""
        page.locator("button.tab:has-text('Logs')").click()
        page.wait_for_timeout(500)
        
        filter_select = page.locator(".log-filter")
        expect(filter_select).to_be_visible()
        
        # Should have options
        options = filter_select.locator("option")
        expect(options).to_have_count(5, timeout=5000)  # ALL, INFO, WARNING, ERROR, DEBUG


@pytest.mark.e2e
@pytest.mark.dashboard
class TestDashboardBenchmarks:
    """Test Benchmarks tab (NEW)."""

    def test_benchmarks_tab_exists(self, page: Page):
        """Verify Benchmarks tab is available."""
        benchmarks_tab = page.locator("button.tab:has-text('Benchmarks')")
        expect(benchmarks_tab).to_be_visible()

    def test_benchmarks_tab_navigation(self, page: Page):
        """Verify Benchmarks tab navigation works."""
        benchmarks_tab = page.locator("button.tab:has-text('Benchmarks')")
        benchmarks_tab.click()
        
        page.wait_for_timeout(500)
        
        expect(benchmarks_tab).to_have_class(re.compile(".*active.*"))
        
        benchmarks_content = page.locator("#benchmarks-tab")
        expect(benchmarks_content).to_have_class(re.compile(".*active.*"))

    def test_benchmark_charts_visible(self, page: Page, take_screenshot):
        """Verify benchmark charts are rendered."""
        page.locator("button.tab:has-text('Benchmarks')").click()
        page.wait_for_timeout(2000)
        
        # Check for canvas elements (Chart.js)
        charts = page.locator("canvas")
        count = charts.count()
        
        assert count > 0, "Should have at least one chart canvas"
        
        take_screenshot("benchmarks_tab")

    def test_benchmark_data_loads(self, page: Page):
        """Verify benchmark data loads from API."""
        with page.expect_response("**/api/benchmarks**") as response_info:
            page.locator("button.tab:has-text('Benchmarks')").click()
        response = response_info.value
        assert response.status == 200, "Benchmarks API should return 200"


@pytest.mark.e2e
@pytest.mark.dashboard
class TestDashboardErrorHandling:
    """Test error handling and edge cases."""

    def test_api_error_displays_message(self, page: Page):
        """Verify API errors are displayed to user."""
        # This test assumes /api/tasks might fail if DB doesn't exist
        # Dashboard should show error message instead of crashing
        
        page.wait_for_timeout(2000)
        
        # Check if error message is shown
        error_msgs = page.locator("td:has-text('Error:')")
        
        # If error, should display gracefully
        if error_msgs.count() > 0:
            expect(error_msgs.first).to_be_visible()
            expect(error_msgs.first).to_contain_text("Error:")

    def test_page_doesnt_crash_on_missing_data(self, page: Page):
        """Verify page handles missing data gracefully."""
        # Navigate through all tabs
        tabs = ["Overview", "Hypotheses", "Tools", "Logs", "Chat", "Benchmarks"]
        
        for tab_name in tabs:
            tab = page.locator(f"button.tab:has-text('{tab_name}')")
            tab.click()
            page.wait_for_timeout(1000)
            
            # Page should still be responsive
            expect(page.locator("h1")).to_be_visible()

    def test_console_no_critical_errors(self, page: Page):
        """Verify no critical JavaScript errors in console."""
        errors = []
        
        def handle_console_message(msg):
            if msg.type == "error":
                errors.append(msg.text)
        
        page.on("console", handle_console_message)
        
        # Navigate through tabs
        page.locator("button.tab:has-text('Hypotheses')").click()
        page.wait_for_timeout(1000)
        
        page.locator("button.tab:has-text('Tools')").click()
        page.wait_for_timeout(1000)
        
        # Should have no critical errors
        critical_errors = [e for e in errors if "critical" in e.lower() or "fatal" in e.lower()]
        assert len(critical_errors) == 0, f"Found critical errors: {critical_errors}"


@pytest.mark.e2e
@pytest.mark.dashboard
@pytest.mark.slow
class TestDashboardPerformance:
    """Test dashboard performance and responsiveness."""

    def test_page_loads_within_timeout(self, page: Page):
        """Verify page loads within acceptable time."""
        start_time = time.time()
        
        page.goto("http://localhost:8000/dashboard")
        page.wait_for_load_state("networkidle")
        
        load_time = time.time() - start_time
        
        assert load_time < 5.0, f"Page took {load_time:.2f}s to load (should be < 5s)"

    def test_tab_switching_responsive(self, page: Page):
        """Verify tab switching is fast and responsive."""
        tabs = ["Overview", "Hypotheses", "Tools", "Logs"]
        
        for tab_name in tabs:
            start_time = time.time()
            
            page.locator(f"button.tab:has-text('{tab_name}')").click()
            page.wait_for_timeout(200)  # Small buffer
            
            switch_time = time.time() - start_time
            
            assert switch_time < 1.0, f"Tab switch to {tab_name} took {switch_time:.2f}s (should be < 1s)"
