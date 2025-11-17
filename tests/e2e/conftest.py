"""
Playwright E2E Test Fixtures

Shared fixtures for dashboard testing:
- Browser setup
- Page navigation
- Dashboard server startup/shutdown
- Authentication (if needed)
"""

import asyncio
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Page, Browser, BrowserContext, expect


# Dashboard server management
@pytest.fixture(scope="session")
def dashboard_server():
    """
    Start dashboard server for testing session.
    
    Yields server process, shuts down after all tests.
    """
    # Check if server already running
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()
    
    if result == 0:
        # Server already running
        print("Dashboard server already running on port 8000")
        yield None
        return
    
    # Determine python executable (prefer current interpreter / env override)
    python_cmd = (
        os.environ.get("PYTHON_EXECUTABLE")
        or os.environ.get("PYTHON")
        or sys.executable
        or shutil.which("python3")
        or shutil.which("python")
    )

    if not python_cmd:
        raise FileNotFoundError("Unable to locate Python interpreter for dashboard server")

    # Start server
    project_root = Path(__file__).parent.parent.parent
    server_script = project_root / "scripts" / "dashboard_server.py"
    
    if not server_script.exists():
        # Fallback: start via run.py
        server_script = project_root / "run.py"
        env = os.environ.copy()
        env["SOPHIA_INTERFACE"] = "webui"
        
        process = subprocess.Popen(
            [python_cmd, str(server_script)],
            cwd=str(project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        process = subprocess.Popen(
            [python_cmd, str(server_script)],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    
    # Wait for server to start
    max_wait = 30
    for _ in range(max_wait):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        if result == 0:
            print("Dashboard server started successfully")
            break
        time.sleep(1)
    else:
        process.kill()
        raise TimeoutError("Dashboard server failed to start within 30 seconds")
    
    yield process
    
    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    print("Dashboard server stopped")


@pytest.fixture(scope="function")
def page(dashboard_server, page: Page) -> Generator[Page, None, None]:
    """
    Navigate to dashboard and return page object.
    
    Automatically navigates to http://localhost:8000/dashboard
    """
    page.goto("http://localhost:8000/dashboard")
    
    # Wait for page to load
    page.wait_for_load_state("networkidle")
    
    yield page


@pytest.fixture(scope="function")
def dashboard_page(page: Page) -> Page:
    """Alias for page fixture with dashboard navigation."""
    return page


# Helper fixtures for common assertions
@pytest.fixture
def assert_element_visible(page: Page):
    """Helper to assert element is visible."""
    def _assert(selector: str, timeout: int = 5000):
        expect(page.locator(selector)).to_be_visible(timeout=timeout)
    return _assert


@pytest.fixture
def assert_element_hidden(page: Page):
    """Helper to assert element is hidden."""
    def _assert(selector: str, timeout: int = 5000):
        expect(page.locator(selector)).to_be_hidden(timeout=timeout)
    return _assert


@pytest.fixture
def assert_text_contains(page: Page):
    """Helper to assert element contains text."""
    def _assert(selector: str, text: str, timeout: int = 5000):
        expect(page.locator(selector)).to_contain_text(text, timeout=timeout)
    return _assert


# Screenshot helper
@pytest.fixture
def take_screenshot(page: Page, request):
    """Take screenshot with test name."""
    def _screenshot(name: str = ""):
        screenshots_dir = Path("screenshots/e2e_tests")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        test_name = request.node.name
        filename = f"{test_name}_{name}.png" if name else f"{test_name}.png"
        filepath = screenshots_dir / filename
        
        page.screenshot(path=str(filepath))
        print(f"Screenshot saved: {filepath}")
        return filepath
    
    return _screenshot
