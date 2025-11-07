"""
Cognitive Browser Control Plugin

Allows SOPHIA to interact with web browsers using Playwright.
Enables autonomous testing, web scraping, and Dashboard self-testing.

Features:
- Navigate to URLs
- Click elements
- Fill forms
- Take screenshots
- Execute JavaScript
- Monitor network traffic
- Test Dashboard functionality
"""

from typing import Any, Dict, Optional
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from pathlib import Path
import asyncio
import json
import time
import logging

logger = logging.getLogger(__name__)


class BrowserControlPlugin(BasePlugin):
    """Browser automation and testing plugin using Playwright."""
    
    def __init__(self):
        super().__init__()
        self.browser = None
        self.context_browser = None  # Renamed to avoid confusion with SharedContext
        self.page = None
        self.screenshots_dir = Path("screenshots/sophia_tests")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.pw = None
        self.playwright = None
        
    @property
    def name(self) -> str:
        return "cognitive_browser_control"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: dict) -> None:
        """Setup browser control plugin."""
        logger.info("🌐 Browser Control plugin initialized")
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """Main execution method - not directly used, browser methods called explicitly."""
        return context
    
    async def _initialize_browser(self):
        """Initialize Playwright browser if not already initialized."""
        if self.pw is None:
            try:
                from playwright.async_api import async_playwright
                self.playwright = async_playwright()
                self.pw = await self.playwright.start()
                logger.info("✅ Playwright initialized")
            except ImportError:
                logger.warning("⚠️ Playwright not installed. Run: pip install playwright && playwright install")
                raise
    
    async def cleanup(self):
        """Cleanup browser resources."""
        if self.page:
            await self.page.close()
        if self.context_browser:
            await self.context_browser.close()
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
    
    async def browser_navigate(self, url: str, headless: bool = True, wait: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            headless: Run browser in headless mode
            wait: Wait condition ('load', 'domcontentloaded', 'networkidle')
            
        Returns:
            Dict with success status and page info
        """
        try:
            await self._initialize_browser()
            
            if not self.browser:
                self.browser = await self.pw.chromium.launch(headless=headless)
                self.context_browser = await self.browser.new_context(viewport={'width': 1920, 'height': 1080})
                self.page = await self.context_browser.new_page()
                
                # Setup console and error logging
                self.page.on("console", lambda msg: logger.debug(f"Browser console: [{msg.type}] {msg.text}"))
                self.page.on("pageerror", lambda exc: logger.error(f"Browser error: {exc}"))
            
            logger.info(f"🌐 Navigating to: {url}")
            await self.page.goto(url, wait_until=wait)
            
            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "message": f"Navigated to {url}"
            }
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def browser_click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """
        Click an element by CSS selector.
        
        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Dict with success status
        """
        try:
            if not self.page:
                return {"success": False, "error": "Browser not initialized. Call browser_navigate first."}
            
            logger.info(f"🖱️ Clicking: {selector}")
            await self.page.click(selector, timeout=timeout)
            
            return {
                "success": True,
                "message": f"Clicked {selector}"
            }
            
        except Exception as e:
            logger.error(f"❌ Click failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def browser_fill(self, selector: str, text: str) -> Dict[str, Any]:
        """
        Fill a form input.
        
        Args:
            selector: CSS selector for input element
            text: Text to fill
            
        Returns:
            Dict with success status
        """
        try:
            if not self.page:
                return {"success": False, "error": "Browser not initialized"}
            
            logger.info(f"⌨️ Filling {selector} with: {text[:50]}...")
            await self.page.fill(selector, text)
            
            return {
                "success": True,
                "message": f"Filled {selector}"
            }
            
        except Exception as e:
            logger.error(f"❌ Fill failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def browser_screenshot(self, name: Optional[str] = None, full_page: bool = True) -> Dict[str, Any]:
        """
        Capture a screenshot.
        
        Args:
            name: Screenshot filename (auto-generated if None)
            full_page: Capture full scrollable page
            
        Returns:
            Dict with success status and screenshot path
        """
        try:
            if not self.page:
                return {"success": False, "error": "Browser not initialized"}
            
            if name is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                name = f"screenshot_{timestamp}.png"
            
            if not name.endswith('.png'):
                name += '.png'
            
            path = self.screenshots_dir / name
            await self.page.screenshot(path=str(path), full_page=full_page)
            
            logger.info(f"📸 Screenshot saved: {path}")
            return {
                "success": True,
                "path": str(path),
                "message": f"Screenshot saved to {path}"
            }
            
        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def browser_get_text(self, selector: str) -> Dict[str, Any]:
        """
        Get text content of an element.
        
        Args:
            selector: CSS selector
            
        Returns:
            Dict with text content
        """
        try:
            if not self.page:
                return {"success": False, "error": "Browser not initialized"}
            
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return {
                    "success": True,
                    "text": text
                }
            else:
                return {
                    "success": False,
                    "error": f"Element not found: {selector}"
                }
                
        except Exception as e:
            logger.error(f"❌ Get text failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def browser_wait_for_selector(self, selector: str, state: str = "visible", timeout: int = 30000) -> Dict[str, Any]:
        """
        Wait for an element to reach a specific state.
        
        Args:
            selector: CSS selector
            state: Element state ('visible', 'hidden', 'attached', 'detached')
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Dict with success status
        """
        try:
            if not self.page:
                return {"success": False, "error": "Browser not initialized"}
            
            logger.info(f"⏳ Waiting for {selector} to be {state}...")
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            
            return {
                "success": True,
                "message": f"Element {selector} is {state}"
            }
            
        except Exception as e:
            logger.error(f"❌ Wait failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def browser_execute_js(self, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript in the page context.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Dict with execution result
        """
        try:
            if not self.page:
                return {"success": False, "error": "Browser not initialized"}
            
            logger.info(f"🔧 Executing JavaScript: {script[:50]}...")
            result = await self.page.evaluate(script)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ JavaScript execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_dashboard(self, url: str = "http://127.0.0.1:8000/dashboard") -> Dict[str, Any]:
        """
        Autonomous self-test of SOPHIA's Dashboard.
        
        Tests:
        - Dashboard loads
        - All tabs accessible (Overview, Chat, Logs, Tools)
        - Stats display correctly
        - Takes screenshots of each tab
        
        Args:
            url: Dashboard URL
            
        Returns:
            Dict with test results
        """
        test_results = {
            "success": True,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "screenshots": [],
            "errors": []
        }
        
        # Initialize browser ONCE at start
        await self._initialize_browser()
        if not self.browser:
            self.browser = await self.pw.chromium.launch(headless=True)
            self.context_browser = await self.browser.new_context(viewport={'width': 1920, 'height': 1080})
            self.page = await self.context_browser.new_page()
        
        try:
            # Test 1: Navigate to Dashboard
            logger.info("🧪 Test 1: Navigating to Dashboard...")
            logger.info(f"🌐 Navigating to: {url}")
            await self.page.goto(url, wait_until="networkidle")
            nav_result = {"success": True, "url": url}
            test_results["total_tests"] += 1
            
            if nav_result["success"]:
                test_results["passed"] += 1
                logger.info("✅ Dashboard loaded successfully")
            else:
                test_results["failed"] += 1
                test_results["errors"].append(f"Navigation failed: {nav_result.get('error')}")
                test_results["success"] = False
                return test_results
            
            # Test 2: Check Overview tab stats
            logger.info("🧪 Test 2: Checking Overview tab stats...")
            test_results["total_tests"] += 1
            
            try:
                # Wait for stats to load
                await self.page.wait_for_selector("#pluginCount", timeout=10000)
                
                # Get stats
                plugin_count = await self.page.text_content("#pluginCount")
                pending_count = await self.page.text_content("#pendingCount")
                
                if plugin_count and pending_count:
                    test_results["passed"] += 1
                    logger.info(f"✅ Stats found: {plugin_count} plugins, {pending_count} pending")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Stats not found")
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Stats check failed: {e}")
            
            # Screenshot Overview tab
            screenshot = await self.browser_screenshot("dashboard_overview_selftest")
            if screenshot["success"]:
                test_results["screenshots"].append(screenshot["path"])
            
            # Test 3: Test Chat tab
            logger.info("🧪 Test 3: Testing Chat tab...")
            test_results["total_tests"] += 1
            
            try:
                await self.browser_click('button:has-text("💬 Chat")')
                await asyncio.sleep(1)
                
                # Check chat interface loaded
                chat_input = await self.page.query_selector("#userInput")
                if chat_input:
                    test_results["passed"] += 1
                    logger.info("✅ Chat tab works")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Chat input not found")
                
                # Screenshot Chat tab
                screenshot = await self.browser_screenshot("dashboard_chat_selftest")
                if screenshot["success"]:
                    test_results["screenshots"].append(screenshot["path"])
                    
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Chat tab test failed: {e}")
            
            # Test 4: Test Logs tab
            logger.info("🧪 Test 4: Testing Logs tab...")
            test_results["total_tests"] += 1
            
            try:
                await self.browser_click('button:has-text("📜 Logs")')
                await asyncio.sleep(1)
                
                # Check logs loaded
                logs = await self.page.query_selector("#logsContent")
                if logs:
                    test_results["passed"] += 1
                    logger.info("✅ Logs tab works")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Logs content not found")
                
                # Screenshot Logs tab
                screenshot = await self.browser_screenshot("dashboard_logs_selftest")
                if screenshot["success"]:
                    test_results["screenshots"].append(screenshot["path"])
                    
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Logs tab test failed: {e}")
            
            # Test 5: Test Tools tab
            logger.info("🧪 Test 5: Testing Tools tab...")
            test_results["total_tests"] += 1
            
            try:
                await self.browser_click('button:has-text("🛠️ Tools")')
                await asyncio.sleep(1)
                
                # Check tools loaded
                tools = await self.page.query_selector("#tools-tab")
                if tools:
                    test_results["passed"] += 1
                    logger.info("✅ Tools tab works")
                else:
                    test_results["failed"] += 1
                    test_results["errors"].append("Tools tab not found")
                
                # Screenshot Tools tab
                screenshot = await self.browser_screenshot("dashboard_tools_selftest")
                if screenshot["success"]:
                    test_results["screenshots"].append(screenshot["path"])
                    
            except Exception as e:
                test_results["failed"] += 1
                test_results["errors"].append(f"Tools tab test failed: {e}")
            
            # Final result
            test_results["success"] = test_results["failed"] == 0
            
            logger.info(f"🎯 Dashboard self-test complete: {test_results['passed']}/{test_results['total_tests']} passed")
            
        except Exception as e:
            logger.error(f"❌ Dashboard test failed: {e}")
            test_results["success"] = False
            test_results["errors"].append(str(e))
        finally:
            # Cleanup browser after test
            if self.page:
                await self.page.close()
                self.page = None
            if self.context_browser:
                await self.context_browser.close()
                self.context_browser = None
            if self.browser:
                await self.browser.close()
                self.browser = None
        
        return test_results
