#!/usr/bin/env python3
"""
Sophie's Jules API Integration Test

This test verifies that Sophie can:
1. Recognize when to use Jules API
2. Call Jules API methods correctly
3. Monitor Jules sessions
4. Process responses appropriately
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 70)
print("SOPHIE + JULES API INTEGRATION TEST")
print("=" * 70)

# Test 1: Can Sophie list Jules sessions?
print("\n" + "-" * 70)
print("TEST 1: List Jules Sessions")
print("-" * 70)
print("Prompt: 'Sophie, use Jules API to list all my coding sessions.'")
print("Expected: Sophie should use tool_jules.list_sessions()")
print("")

import subprocess

result = subprocess.run(
    [
        sys.executable,
        "run.py",
        "Sophie, use Jules API to list all my coding sessions. Show me the results.",
    ],
    cwd=str(project_root),
    capture_output=True,
    text=True,
    timeout=60,
)

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

# Check if tool_jules was mentioned in logs
log_file = project_root / "logs" / "sophia.log"
if log_file.exists():
    with open(log_file, "r") as f:
        log_content = f.read()
        if "tool_jules" in log_content:
            print("\n✅ TEST 1 PASSED: Sophie used tool_jules plugin")
        else:
            print("\n❌ TEST 1 FAILED: tool_jules not found in logs")
            print("Sophie might not know about Jules API plugin yet.")

# Test 2: Can Sophie understand Jules session structure?
print("\n" + "-" * 70)
print("TEST 2: Understanding Jules API Responses")
print("-" * 70)
print("Prompt: 'What can you tell me about Jules API capabilities?'")
print("Expected: Sophie should reference docs/JULES_API_DOCUMENTATION.md")
print("")

result2 = subprocess.run(
    [
        sys.executable,
        "run.py",
        "What can you tell me about Jules API? What methods are available in the tool_jules plugin?",
    ],
    cwd=str(project_root),
    capture_output=True,
    text=True,
    timeout=60,
)

print("STDOUT:")
print(result2.stdout)

# Test 3: Can Sophie create a session (dry run)?
print("\n" + "-" * 70)
print("TEST 3: Session Creation Planning")
print("-" * 70)
print("Prompt: 'Explain how to create a Jules coding session'")
print("Expected: Sophie should describe create_session() method")
print("")

result3 = subprocess.run(
    [
        sys.executable,
        "run.py",
        "Sophie, explain step-by-step how to use Jules API to create a new coding session. What parameters are needed?",
    ],
    cwd=str(project_root),
    capture_output=True,
    text=True,
    timeout=60,
)

print("STDOUT:")
print(result3.stdout)

print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("Review the outputs above to verify Sophie's Jules API integration.")
print("")
print("✅ Check if Sophie can:")
print("   1. List sessions using tool_jules")
print("   2. Understand Jules API structure")
print("   3. Explain session creation process")
print("")
print("📄 Full logs available in: logs/sophia.log")
print("=" * 70)
