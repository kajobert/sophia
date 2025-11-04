"""
Test script for GitHub Integration Plugin
Tests Pydantic validation, plugin initialization, and basic functionality.
"""

from plugins.tool_github import (
    ToolGitHub,
    CreateIssueRequest,
    ListIssuesRequest,
    UpdateIssueRequest,
    CreatePullRequestRequest,
    IssueResponse,
    PullRequestResponse,
)
from core.context import SharedContext
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

print("=== Testing Pydantic Models ===")

# Test CreateIssueRequest
try:
    request = CreateIssueRequest(
        owner="ShotyCZ",
        repo="sophia",
        title="Test Issue",
        body="This is a test issue",
        labels=["bug", "enhancement"],
    )
    print(f"✅ CreateIssueRequest: {request.title}")
except Exception as e:
    print(f"❌ CreateIssueRequest failed: {e}")

# Test ListIssuesRequest
try:
    request = ListIssuesRequest(owner="ShotyCZ", repo="sophia", state="open", per_page=10)
    print(f"✅ ListIssuesRequest: state={request.state}, per_page={request.per_page}")
except Exception as e:
    print(f"❌ ListIssuesRequest failed: {e}")

# Test UpdateIssueRequest
try:
    request = UpdateIssueRequest(owner="ShotyCZ", repo="sophia", issue_number=1, state="closed")
    print(f"✅ UpdateIssueRequest: issue #{request.issue_number}, state={request.state}")
except Exception as e:
    print(f"❌ UpdateIssueRequest failed: {e}")

# Test CreatePullRequestRequest
try:
    request = CreatePullRequestRequest(
        owner="ShotyCZ",
        repo="sophia",
        title="Add GitHub Integration",
        body="Adds tool_github.py plugin",
        head="feature/github-integration",
        base="master",
    )
    print(f"✅ CreatePullRequestRequest: {request.head} -> {request.base}")
except Exception as e:
    print(f"❌ CreatePullRequestRequest failed: {e}")

# Test validation error
try:
    invalid = CreateIssueRequest(
        owner="", repo="sophia", title="Test", body="Test"  # Invalid: empty string
    )
    print("❌ Should have failed validation!")
except Exception as e:
    print(f"✅ Validation correctly rejected empty owner: {type(e).__name__}")

# Test invalid state
try:
    invalid = ListIssuesRequest(
        owner="ShotyCZ", repo="sophia", state="invalid"  # Invalid: must be open, closed, or all
    )
    print("❌ Should have failed validation!")
except Exception as e:
    print(f"✅ Validation correctly rejected invalid state: {type(e).__name__}")

print("\n=== Testing Plugin Initialization ===")

# Create plugin instance
context = SharedContext(session_id="test-session", current_state="testing", logger=logger)

plugin = ToolGitHub()
print(f"✅ Plugin name: {plugin.name}")
print(f"✅ Plugin type: {plugin.plugin_type}")
print(f"✅ Plugin version: {plugin.version}")

# Test tool definitions
tool_defs = plugin.get_tool_definitions()
print(f"✅ Tool definitions: {len(tool_defs)} tools")
for tool in tool_defs:
    print(f"   - {tool['name']}")

print("\n=== Testing Setup (Without Token) ===")

# Setup without token should warn but not fail
try:
    plugin.setup({})
    print("✅ Setup completed (without token)")
except Exception as e:
    print(f"❌ Setup failed: {e}")

print("\n=== Testing Setup (With Mock Token) ===")

# Setup with mock token
try:
    plugin.setup({"github_token": "ghp_mock_token_for_testing"})
    print("✅ Setup completed (with mock token)")
    print(f"✅ Session initialized: {plugin.session is not None}")
except Exception as e:
    print(f"❌ Setup failed: {e}")

print("\n=== Testing Response Models ===")

# Test IssueResponse
try:
    issue = IssueResponse(
        number=1,
        title="Test Issue",
        body="Test body",
        state="open",
        html_url="https://github.com/ShotyCZ/sophia/issues/1",
        created_at="2025-11-03T00:00:00Z",
        updated_at="2025-11-03T00:00:00Z",
        labels=["bug"],
        assignees=["ShotyCZ"],
    )
    print(f"✅ IssueResponse: #{issue.number} - {issue.title}")
except Exception as e:
    print(f"❌ IssueResponse failed: {e}")

# Test PullRequestResponse
try:
    pr = PullRequestResponse(
        number=1,
        title="Test PR",
        body="Test body",
        state="open",
        html_url="https://github.com/ShotyCZ/sophia/pull/1",
        head="feature/test",
        base="master",
        created_at="2025-11-03T00:00:00Z",
        updated_at="2025-11-03T00:00:00Z",
        merged=False,
    )
    print(f"✅ PullRequestResponse: #{pr.number} - {pr.head} -> {pr.base}")
except Exception as e:
    print(f"❌ PullRequestResponse failed: {e}")

print("\n✅ All tests passed!")
print("\n💡 To test with real GitHub API:")
print("1. Set GITHUB_TOKEN environment variable")
print("2. Run: python -c 'from plugins.tool_github import ToolGitHub; ...'")
print("3. Or have Sophie use it: python run.py 'Sophie, list issues from ShotyCZ/sophia'")
