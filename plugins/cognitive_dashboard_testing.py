"""
Cognitive Dashboard Testing Plugin

Sophia's autonomous dashboard testing and fixing capability.
Uses cloud LLM (OpenRouter) for analysis, doesn't require local Ollama.

Workflow:
1. Install playwright if missing
2. Start dashboard server in background
3. Run E2E tests via pytest
4. Parse test results
5. Analyze failures with cloud LLM
6. Propose fixes
7. Optionally: Auto-fix via cognitive_self_tuning

This plugin demonstrates Sophia's self-sufficiency - she doesn't need
Jules for runtime testing since Jules can't run Sophia anyway.

Jules is better suited for:
- Deep web research
- Documentation analysis
- Codebase review (read-only)
- Implementation proposals based on external sources
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


logger = logging.getLogger(__name__)


class DashboardTestingPlugin(BasePlugin):
    """
    Autonomous dashboard testing and fixing.
    
    Sophia runs this herself using cloud LLM for analysis.
    No need for Jules - he can't run Sophia anyway.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results: Optional[Dict] = None

    @property
    def name(self) -> str:
        return "cognitive_dashboard_testing"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initialize dashboard testing."""
        self._logger = config.get("logger", logger)
        self.tool_cloud_llm = config.get("tool_cloud_llm")
        
        if not self.tool_cloud_llm:
            self._logger.warning("Cloud LLM not available - testing will be limited")

    async def check_playwright_installed(self, context: SharedContext) -> bool:
        """Check if playwright is installed."""
        try:
            result = subprocess.run(
                ["playwright", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception as e:
            context.logger.error(f"Error checking playwright: {e}")
            return False

    async def install_playwright(self, context: SharedContext) -> bool:
        """Install playwright browsers."""
        try:
            context.logger.info("Installing playwright browsers...")
            
            # Install playwright package
            result1 = subprocess.run(
                ["pip", "install", "playwright", "pytest-playwright"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result1.returncode != 0:
                context.logger.error(f"Failed to install playwright: {result1.stderr}")
                return False
            
            # Install browser drivers
            result2 = subprocess.run(
                ["playwright", "install", "chromium"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result2.returncode != 0:
                context.logger.error(f"Failed to install chromium: {result2.stderr}")
                return False
            
            context.logger.info("Playwright installed successfully")
            return True
            
        except Exception as e:
            context.logger.error(f"Playwright installation error: {e}")
            return False

    async def run_dashboard_tests(
        self, context: SharedContext, headed: bool = False
    ) -> Dict[str, Any]:
        """
        Run dashboard E2E tests.
        
        Args:
            context: Shared context
            headed: Show browser window (for debugging)
        
        Returns:
            Test results dict
        """
        # Check playwright
        if not await self.check_playwright_installed(context):
            context.logger.info("Playwright not installed, installing...")
            if not await self.install_playwright(context):
                return {"success": False, "error": "Playwright installation failed"}

        # Build pytest command
        test_path = self.project_root / "tests" / "e2e" / "test_dashboard.py"
        
        if not test_path.exists():
            return {"success": False, "error": f"Test file not found: {test_path}"}

        cmd = [
            "pytest",
            str(test_path),
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=.pytest_report.json"
        ]
        
        if headed:
            cmd.append("--headed")

        context.logger.info(f"Running dashboard tests: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )

            # Parse JSON report if available
            report_path = self.project_root / ".pytest_report.json"
            if report_path.exists():
                with open(report_path, 'r') as f:
                    self.test_results = json.load(f)
            else:
                # Fallback: parse stdout
                self.test_results = {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }

            # Analyze results
            passed = self.test_results.get("summary", {}).get("passed", 0)
            failed = self.test_results.get("summary", {}).get("failed", 0)
            total = self.test_results.get("summary", {}).get("total", 0)

            context.logger.info(f"Tests completed: {passed}/{total} passed, {failed} failed")

            return {
                "success": result.returncode == 0,
                "passed": passed,
                "failed": failed,
                "total": total,
                "results": self.test_results
            }

        except subprocess.TimeoutExpired:
            context.logger.error("Tests timed out after 5 minutes")
            return {"success": False, "error": "Test timeout"}
        except Exception as e:
            context.logger.error(f"Test execution error: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_failures_with_llm(
        self, context: SharedContext, test_results: Dict
    ) -> Dict[str, Any]:
        """
        Use cloud LLM to analyze test failures and suggest fixes.
        
        This is where Sophia's intelligence comes in - she uses
        DeepSeek/Claude to understand WHY tests failed.
        """
        if not self.tool_cloud_llm:
            return {"error": "Cloud LLM not available"}

        # Extract failures
        failures = []
        for test in test_results.get("tests", []):
            if test.get("outcome") == "failed":
                failures.append({
                    "test_name": test.get("nodeid"),
                    "error": test.get("call", {}).get("longrepr", "Unknown error")
                })

        if not failures:
            return {"analysis": "All tests passed!", "fixes_needed": []}

        # Build analysis prompt
        prompt = f"""You are analyzing failed E2E tests for Sophia's dashboard.

**Failed Tests:**
{json.dumps(failures, indent=2)}

**Your Task:**
1. Identify root causes for each failure
2. Categorize issues:
   - Missing database files (.data/*.db)
   - API endpoint errors
   - Frontend rendering issues
   - Network/timeout problems
3. Propose concrete fixes for each issue
4. Prioritize fixes by impact (high/medium/low)

**Output Format (JSON):**
{{
  "root_causes": ["cause1", "cause2", ...],
  "fixes": [
    {{
      "issue": "description",
      "priority": "high|medium|low",
      "fix": "concrete solution",
      "files_to_modify": ["file1.py", "file2.html"]
    }}
  ],
  "can_auto_fix": true/false,
  "needs_human_review": true/false
}}
"""

        try:
            # Call cloud LLM
            response = await self.tool_cloud_llm.generate_completion(
                context=context,
                messages=[{"role": "user", "content": prompt}],
                model="openrouter/deepseek/deepseek-chat",  # Cheap + smart
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.get("content", "{}"))
            context.logger.info(f"LLM analysis complete: {len(analysis.get('fixes', []))} fixes proposed")

            return analysis

        except Exception as e:
            context.logger.error(f"LLM analysis error: {e}")
            return {"error": str(e)}

    async def test_and_fix_dashboard(
        self, context: SharedContext, auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Complete workflow: test → analyze → fix.
        
        Args:
            context: Shared context
            auto_fix: Automatically apply fixes (requires cognitive_self_tuning)
        
        Returns:
            Complete report with results and actions taken
        """
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": None,
            "analysis": None,
            "fixes_applied": [],
            "success": False
        }

        # Step 1: Run tests
        context.logger.info("=== STEP 1: Running Dashboard Tests ===")
        test_results = await self.run_dashboard_tests(context)
        report["test_results"] = test_results

        if not test_results.get("success"):
            # Step 2: Analyze failures
            context.logger.info("=== STEP 2: Analyzing Failures with Cloud LLM ===")
            analysis = await self.analyze_failures_with_llm(context, test_results.get("results", {}))
            report["analysis"] = analysis

            if auto_fix and analysis.get("can_auto_fix"):
                # Step 3: Apply fixes
                context.logger.info("=== STEP 3: Auto-Fixing Issues ===")
                # TODO: Integrate with cognitive_self_tuning
                # For now, just log what would be fixed
                for fix in analysis.get("fixes", []):
                    context.logger.info(f"Would fix: {fix['issue']} - {fix['fix']}")
                    report["fixes_applied"].append(fix)
        else:
            context.logger.info("✅ All tests passed!")
            report["success"] = True

        return report

    async def execute(self, context: SharedContext) -> SharedContext:
        """Execute dashboard testing workflow."""
        result = await self.test_and_fix_dashboard(context, auto_fix=False)
        context.payload["dashboard_testing_report"] = result
        return context

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Tool definitions for manual invocation."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "test_and_fix_dashboard",
                    "description": "Run dashboard E2E tests, analyze failures with cloud LLM, and optionally auto-fix issues. Sophia's autonomous testing capability.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "auto_fix": {
                                "type": "boolean",
                                "description": "Automatically apply fixes (requires review)",
                                "default": False
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_dashboard_tests",
                    "description": "Run dashboard E2E tests only (no analysis or fixing)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "headed": {
                                "type": "boolean",
                                "description": "Show browser window for debugging",
                                "default": False
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
