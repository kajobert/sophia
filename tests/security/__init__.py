"""
Security test suite for Sophia V2.

This package contains comprehensive security tests for the Phase 0 
emergency patches that protect against critical vulnerabilities.

Test Coverage:
- test_path_traversal.py: Path traversal and protected paths (Attack #3)
- test_command_injection.py: Command injection and DoS (Attack #1, #5)
- test_plan_validation.py: LLM plan injection (Attack #1)

All tests should pass before deploying Roadmap 04 autonomous features.
"""
