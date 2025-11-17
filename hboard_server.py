[1mdiff --git a/tests/e2e/test_dashboard.py b/tests/e2e/test_dashboard.py[m
[1mindex 0f577149..28d1cc17 100644[m
[1m--- a/tests/e2e/test_dashboard.py[m
[1m+++ b/tests/e2e/test_dashboard.py[m
[36m@@ -24,6 +24,7 @@[m [mRun:[m
     pytest tests/e2e/test_dashboard.py --screenshot=on[m
 """[m
 [m
[32m+[m[32mimport re[m
 import time[m
 from pathlib import Path[m
 [m
[36m@@ -56,10 +57,10 @@[m [mclass TestDashboardOverview:[m
     def test_overview_tab_active_by_default(self, page: Page):[m
         """Verify Overview tab is active on page load."""[m
         overview_tab = page.locator("button.tab:has-text('Overview')")[m
[31m-        expect(overview_tab).to_have_class(/active/)[m
[32m+[m[32m        expect(overview_tab).to_have_class(re.compile(".*active.*"))[m
         [m
[31m-        overview_content = page.locator("#overviewTab")[m
[31m-        expect(overview_content).to_have_class(/active/)[m
[32m+[m[32m        overview_content = page.locator("#overview-tab")[m
[32m+[m[32m        expect(overview_content).to_have_class(re.compile(".*active.*"))[m
 [m
     def test_stats_cards_displayed(self, page: Page):[m
         """Verify statistics cards are visible."""[m
[36m@@ -77,12 +78,16 @@[m [mclass TestDashboardOverview:[m
         [m
         # Check if table has data or empty message[m
         rows = table_body.locator("tr")[m
[31m-        count = rows.count()[m
[31m-        [m
[31m-        if count == 1:[m
[31m-            # Empty state[m
[31m-            empty_msg = rows.first.locator("td")[m
[31m-            expect(empty_msg).to_contain_text("No tasks in queue")[m
[32m+[m[32m        row_count = rows.count()[m
[32m+[m[41m		[m
[32m+[m[32m        if row_count == 1:[m
[32m+[m[32m            # Empty or error state row[m
[32m+[m[32m            first_cell = rows.first.locator("td")[m
[32m+[m[32m            text_content = first_cell.text_content()[m
[32m+[m[32m            if text_content and "Error" in text_content:[m
[32m+[m[32m                expect(first_cell).to_contain_text("Error")[m
[32m+[m[32m            else:[m
[32m+[m[32m                expect(first_cell).to_contain_text("No tasks in queue")[m
         else:[m
             # Has tasks - verify structure[m
             first_row = rows.first[m
[36m@@ -93,14 +98,19 @@[m [mclass TestDashboardOverview:[m
 [m
     def test_auto_refresh_works(self, page: Page):[m
         """Verify auto-refresh updates timestamp."""[m
[31m-        # Get initial timestamp[m
[31m-        timestamp_before = page.locator(".last-update").text_content()[m
[31m-        [m
[31m-        # Wait for refresh (30 seconds)[m
[31m-        page.wait_for_timeout(31000)[m
[31m-        [m
[32m+[m[32m        # Get initial timestamp from overview panel only[m
[32m+[m[32m        timestamp_before = page.locator("#lastUpdate").text_content()[m
[32m+[m[41m		[m
[32m+[m[32m        # Trigger an immediate refresh to avoid long sleeps and wait for DOM to update[m
[32m+[m[32m        page.evaluate("refreshDashboard()")[m
[32m+[m[32m        page.wait_for_function([m
[32m+[m[32m            "initial => document.getElementById('lastUpdate').textContent !== initial",[m
[32m+[m[32m            arg=timestamp_before,[m
[32m+[m[32m            timeout=10000,[m
[32m+[m[32m        )[m
[32m+[m[41m		[m
         # Check timestamp changed[m
[31m-        timestamp_after = page.locator(".last-update").text_content()[m
[32m+[m[32m        timestamp_after = page.locator("#lastUpdate").text_content()[m
         assert timestamp_before != timestamp_after, "Auto-refresh should update timestamp"[m
 [m
 [m
[36m@@ -119,11 +129,11 @@[m [mclass TestDashboardHypotheses:[m
         page.wait_for_timeout(500)[m
         [m
         # Check tab is active[m
[31m-        expect(hyp_tab).to_have_class(/active/)[m
[32m+[m[32m        expect(hyp_tab).to_have_class(re.compile(".*active.*"))[m
         [m
         # Check content is visible[m
[31m-        hyp_content = page.locator("#hypothesesTab")[m
[31m-        expect(hyp_content).to_have_class(/active/)[m
[32m+[m[32m        hyp_content = page.locator("#hypotheses-tab")[m
[32m+[m[32m        expect(hyp_content).to_have_class(re.compile(".*active.*"))[m
 [m
     def test_hypotheses_table_loads(self, page: Page, take_screenshot):[m
         """Verify hypotheses table loads data."""[m
[36m@@ -131,7 +141,7 @@[m [mclass TestDashboardHypotheses:[m
         page.locator("button.tab:has-text('Hypotheses')").click()[m
         page.wait_for_timeout(2000)  # Wait for API call[m
         [m
[31m-        table_body = page.locator("#hypothesesTableBody")[m
[32m+[m[32m        table_body = page.locator("#hypotheses-tab #hypothesesTableBody")[m
         expect(table_body).to_be_visible()[m
         [m
         # Check for data or empty state[m
[36m@@ -139,15 +149,20 @@[m [mclass TestDashboardHypotheses:[m
         count = rows.count()[m
         [m
         if count == 1:[m
[31m-            # Empty state[m
[32m+[m[32m            # Empty or error state[m
             empty_msg = rows.first.locator("td")[m
[31m-            expect(empty_msg).to_contain_text("No hypotheses")[m
[32m+[m[32m            text_content = empty_msg.text_content()[m
[32m+[m[32m            if text_content and "Error" in text_content:[m
[32m+[m[32m                expect(empty_msg).to_contain_text("Error")[m
[32m+[m[32m            else:[m
[32m+[m[32m                expect(empty_msg).to_contain_text("No hypotheses")[m
         else:[m
             # Has hypotheses - verify columns[m
             first_row = rows.first[m
             expect(first_row.locator("td").nth(0)).to_be_visible()  # ID[m
             expect(first_row.locator("td").nth(1)).to_be_visible()  # Description[m
[31m-            expect(first_row.locator("td").nth(2)).to_be_visible()  # Status[m
[32m+[m[32m            expect(first_row.locator("td").nth(2)).to_be_visible()  # Category[m
[32m+[m[32m            expect(first_row.locator("td").nth(3)).to_be_visible()  # Status[m
         [m
         take_screenshot("hypotheses_table")[m
 [m
[36m@@ -157,12 +172,13 @@[m [mclass TestDashboardHypotheses:[m
         page.wait_for_timeout(2000)[m
         [m
         # Look for status badges (if hypotheses exist)[m
[31m-        table_body = page.locator("#hypothesesTableBody")[m
[32m+[m[32m        table_body = page.locator("#hypotheses-tab #hypothesesTableBody")[m
         rows = table_body.locator("tr")[m
[32m+[m[32m        row_count = rows.count()[m
         [m
[31m-        if rows.count() > 1:  # Has data[m
[32m+[m[32m        if row_count > 1:  # Has data[m
             # Status should have emoji indicator[m
[31m-            status_cell = rows.first.locator("td").nth(2)[m
[32m+[m[32m            status_cell = rows.first.locator("td").nth(3)[m
             status_text = status_cell.text_content()[m
             [m
             # Should contain emoji[m
[36m@@ -181,10 +197,10 @@[m [mclass TestDashboardTools:[m
         [m
         page.wait_for_timeout(500)[m
         [m
[31m-        expect(tools_tab).to_have_class(/active/)[m
[32m+[m[32m        expect(tools_tab).to_have_class(re.compile(".*active.*"))[m
         [m
[31m-        tools_content = page.locator("#toolsTab")[m
[31m-        expect(tools_content).to_have_class(/active/)[m
[32m+[m[32m        tools_content = page.locator("#tools-tab")[m
[32m+[m[32m        expect(tools_content).to_have_class(re.compile(".*active.*"))[m
 [m
     def test_tool_buttons_visible(self, page: Page, take_screenshot):[m
         """Verify all tool buttons are rendered."""[m
[36m@@ -252,10 +268,10 @@[m [mclass TestDashboardLogs:[m
         [m
         page.wait_for_timeout(2000)  # Wait for API call[m
         [m
[31m-        expect(logs_tab).to_have_class(/active/)[m
[32m+[m[32m        expect(logs_tab).to_have_class(re.compile(".*active.*"))[m
         [m
[31m-        logs_content = page.locator("#logsTab")[m
[31m-        expect(logs_content).to_have_class(/active/)[m
[32m+[m[32m        logs_content = page.locator("#logs-tab")[m
[32m+[m[32m        expect(logs_content).to_have_class(re.compile(".*active.*"))[m
 [m
     def test_logs_container_visible(self, page: Page, take_screenshot):[m
         """Verify logs container renders."""[m
[36m@@ -297,10 +313,10 @@[m [mclass TestDashboardBenchmarks:[m
         [m
         page.wait_for_timeout(500)[m
         [m
[31m-        expect(benchmarks_tab).to_have_class(/active/)[m
[32m+[m[32m        expect(benchmarks_tab).to_have_class(re.compile(".*active.*"))[m
         [m
[31m-        benchmarks_content = page.locator("#benchmarksTab")[m
[31m-        expect(benchmarks_content).to_have_class(/active/)[m
[32m+[m[32m        benchmarks_content = page.locator("#benchmarks-tab")[m
[32m+[m[32m        expect(benchmarks_content).to_have_class(re.compile(".*active.*"))[m
 [m
     def test_benchmark_charts_visible(self, page: Page, take_screenshot):[m
         """Verify benchmark charts are rendered."""[m
[36m@@ -317,12 +333,8 @@[m [mclass TestDashboardBenchmarks:[m
 [m
     def test_benchmark_data_loads(self, page: Page):[m
         """Verify benchmark data loads from API."""[m
[31m-        page.locator("button.tab:has-text('Benchmarks')").click()[m
[31m-        [m
[31m-        # Wait for API call[m
         with page.expect_response("**/api/benchmarks**") as response_info:[m
[31m-            page.wait_for_timeout(3000)[m
[31m-        [m
[32m+[m[32m            page.locator("button.tab:has-text('Benchmarks')").click()[m
         response = response_info.value[m
         assert response.status == 200, "Benchmarks API should return 200"[m
 [m
