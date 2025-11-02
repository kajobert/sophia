#!/usr/bin/env python3
"""
Test script demonstrating Pydantic validation in Jules API plugin.

This script shows:
1. How Pydantic models validate data automatically
2. How invalid data is rejected with clear error messages
3. Type safety benefits of using Pydantic
"""

from plugins.tool_jules import (
    JulesSession,
    JulesSessionList,
    JulesSource,
    JulesSourceList,
    CreateSessionRequest,
    JulesValidationError
)
from pydantic import ValidationError


def test_session_model():
    """Test JulesSession Pydantic model."""
    print("=" * 60)
    print("TEST 1: JulesSession Model Validation")
    print("=" * 60)
    
    # Valid session
    try:
        session = JulesSession(
            name="sessions/abc123",
            title="Test Session",
            prompt="Create a Flask app",
            state="ACTIVE"
        )
        print("✅ Valid session created:")
        print(f"   ID: {session.name}")
        print(f"   Title: {session.title}")
        print(f"   State: {session.state}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Invalid session name (doesn't start with 'sessions/')
    try:
        bad_session = JulesSession(
            name="invalid/format",
            title="Bad Session"
        )
        print("❌ Should have failed validation!")
    except ValidationError as e:
        print(f"✅ Correctly rejected invalid session name:")
        print(f"   Error: {e.errors()[0]['msg']}")
    
    print()


def test_create_session_request():
    """Test CreateSessionRequest Pydantic model."""
    print("=" * 60)
    print("TEST 2: CreateSessionRequest Validation")
    print("=" * 60)
    
    # Valid request
    try:
        request = CreateSessionRequest(
            prompt="Add authentication to my app",
            source="sources/github/myorg/myrepo",
            branch="develop",
            title="Auth Feature",
            auto_pr=True
        )
        print("✅ Valid create request:")
        print(f"   Source: {request.source}")
        print(f"   Branch: {request.branch}")
        print(f"   Auto PR: {request.auto_pr}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Empty prompt
    try:
        bad_request = CreateSessionRequest(
            prompt="",
            source="sources/github/owner/repo"
        )
        print("❌ Should have rejected empty prompt!")
    except ValidationError as e:
        print(f"✅ Correctly rejected empty prompt:")
        print(f"   Error: {e.errors()[0]['type']}")
    
    # Invalid source format
    try:
        bad_request = CreateSessionRequest(
            prompt="Test",
            source="invalid/format/here"
        )
        print("❌ Should have rejected invalid source!")
    except ValidationError as e:
        print(f"✅ Correctly rejected invalid source format:")
        print(f"   Error: String should match pattern")
    
    print()


def test_session_list():
    """Test JulesSessionList Pydantic model."""
    print("=" * 60)
    print("TEST 3: JulesSessionList Validation")
    print("=" * 60)
    
    # Valid session list
    try:
        session_list = JulesSessionList(
            sessions=[
                {"name": "sessions/123", "title": "Session 1", "state": "ACTIVE"},
                {"name": "sessions/456", "title": "Session 2", "state": "COMPLETED"}
            ],
            next_page_token="token123"
        )
        print(f"✅ Valid session list with {len(session_list.sessions)} sessions:")
        for session in session_list.sessions:
            print(f"   - {session.name}: {session.title} ({session.state})")
        print(f"   Next page token: {session_list.next_page_token}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Empty list (valid)
    try:
        empty_list = JulesSessionList()
        print(f"✅ Valid empty session list:")
        print(f"   Sessions: {len(empty_list.sessions)}")
        print(f"   Next page token: {empty_list.next_page_token}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print()


def test_type_safety():
    """Demonstrate type safety benefits."""
    print("=" * 60)
    print("TEST 4: Type Safety Benefits")
    print("=" * 60)
    
    session = JulesSession(
        name="sessions/test123",
        title="My Session",
        state="ACTIVE"
    )
    
    # Type hints work in IDE
    print(f"✅ IDE knows session.name is a string: '{session.name}'")
    print(f"✅ IDE knows session.title is Optional[str]: '{session.title}'")
    print(f"✅ Autocomplete works for all fields")
    
    # Accessing non-existent field raises AttributeError (not KeyError like dict)
    try:
        _ = session.nonexistent_field
        print("❌ Should have raised AttributeError")
    except AttributeError:
        print("✅ Correctly raises AttributeError for non-existent field")
    
    print()


def test_model_serialization():
    """Test Pydantic model serialization."""
    print("=" * 60)
    print("TEST 5: Model Serialization")
    print("=" * 60)
    
    session = JulesSession(
        name="sessions/abc123",
        title="Test Session",
        prompt="Build a web app",
        state="ACTIVE",
        create_time="2025-11-02T12:00:00Z"
    )
    
    # Convert to dict
    session_dict = session.model_dump()
    print("✅ Model serialized to dict:")
    print(f"   {session_dict}")
    
    # Convert to JSON
    session_json = session.model_dump_json(indent=2)
    print("✅ Model serialized to JSON:")
    print(f"   {session_json}")
    
    # Exclude None values
    session_dict_clean = session.model_dump(exclude_none=True)
    print("✅ Model serialized excluding None:")
    print(f"   {session_dict_clean}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("JULES API PYDANTIC VALIDATION TEST SUITE")
    print("=" * 60 + "\n")
    
    test_session_model()
    test_create_session_request()
    test_session_list()
    test_type_safety()
    test_model_serialization()
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    print("\n✅ Pydantic integration provides:")
    print("   • Automatic data validation")
    print("   • Clear error messages")
    print("   • Type safety and IDE support")
    print("   • Easy serialization/deserialization")
    print("   • Runtime type checking")
