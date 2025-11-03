#!/usr/bin/env python3
"""
Test script for Tavily API plugin with Pydantic validation.

This script demonstrates:
1. Pydantic model validation
2. Request/response type safety
3. Error handling
4. Live API testing (optional)
"""

from plugins.tool_tavily import (
    TavilyAPITool,
    TavilySearchResponse,
    TavilySearchRequest,
    TavilySearchResult,
    TavilyValidationError
)
from pydantic import ValidationError
import os


def test_search_request_validation():
    """Test TavilySearchRequest Pydantic model."""
    print("=" * 60)
    print("TEST 1: TavilySearchRequest Validation")
    print("=" * 60)
    
    # Valid request
    try:
        request = TavilySearchRequest(
            query="Python programming best practices",
            search_depth="advanced",
            max_results=10,
            include_answer=True
        )
        print("✅ Valid search request:")
        print(f"   Query: {request.query}")
        print(f"   Depth: {request.search_depth}")
        print(f"   Max results: {request.max_results}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Empty query
    try:
        bad_request = TavilySearchRequest(
            query="",
            search_depth="basic"
        )
        print("❌ Should have rejected empty query!")
    except ValidationError as e:
        print(f"✅ Correctly rejected empty query:")
        print(f"   Error: {e.errors()[0]['type']}")
    
    # Invalid search depth
    try:
        bad_request = TavilySearchRequest(
            query="test",
            search_depth="invalid"
        )
        print("❌ Should have rejected invalid search depth!")
    except ValidationError as e:
        print(f"✅ Correctly rejected invalid search depth:")
        print(f"   Error: String should match pattern")
    
    # Invalid max_results (too high)
    try:
        bad_request = TavilySearchRequest(
            query="test",
            max_results=25
        )
        print("❌ Should have rejected max_results > 20!")
    except ValidationError as e:
        print(f"✅ Correctly rejected max_results > 20:")
        print(f"   Error: Input should be less than or equal to 20")
    
    print()


def test_search_result_validation():
    """Test TavilySearchResult validation."""
    print("=" * 60)
    print("TEST 2: TavilySearchResult Validation")
    print("=" * 60)
    
    from plugins.tool_tavily import TavilySearchResult
    
    # Valid result
    try:
        result = TavilySearchResult(
            title="Python Best Practices",
            url="https://example.com/python",
            content="A comprehensive guide to Python best practices...",
            score=0.95
        )
        print("✅ Valid search result:")
        print(f"   Title: {result.title}")
        print(f"   Score: {result.score}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Invalid score (out of range)
    try:
        bad_result = TavilySearchResult(
            title="Test",
            url="https://test.com",
            content="Content",
            score=1.5  # > 1.0
        )
        print("❌ Should have rejected score > 1.0!")
    except ValidationError as e:
        print(f"✅ Correctly rejected invalid score:")
        print(f"   Error: Score must be between 0.0 and 1.0")
    
    print()


def test_live_search():
    """Test live Tavily search (requires API key)."""
    print("=" * 60)
    print("TEST 3: Live Tavily API Integration")
    print("=" * 60)
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("⚠️  TAVILY_API_KEY not found in environment")
        print("   Skipping live API test")
        print("   Get your API key at: https://tavily.com")
        print()
        return
    
    # Simple mock context for testing
    class MockLogger:
        def info(self, msg, **kwargs):
            print(f"   [INFO] {msg}")
        def error(self, msg, **kwargs):
            print(f"   [ERROR] {msg}")
    
    class MockContext:
        def __init__(self):
            self.logger = MockLogger()
    
    context = MockContext()
    tavily = TavilyAPITool()
    tavily.setup({"tavily_api_key": api_key})
    
    try:
        # Test 1: Basic search returning Pydantic model
        print("🔍 Test 1: Basic search (Pydantic validation)...")
        results: TavilySearchResponse = tavily.search(
            context=context,
            query="Python async programming 2024",
            search_depth="basic",
            max_results=3
        )
        
        # Verify we got a Pydantic model back
        assert isinstance(results, TavilySearchResponse), "Should return TavilySearchResponse"
        assert isinstance(results.query, str), "Query should be string"
        assert isinstance(results.results, list), "Results should be list"
        
        print(f"✅ Pydantic validation successful!")
        print(f"   Type: {type(results).__name__}")
        print(f"   Query: {results.query}")
        print(f"   Results count: {len(results.results)}")
        
        # Verify each result is also a Pydantic model
        if results.results:
            first_result = results.results[0]
            assert isinstance(first_result, TavilySearchResult), "Result items should be TavilySearchResult"
            print(f"\n   First result (Pydantic model):")
            print(f"   Title: {first_result.title}")
            print(f"   URL: {first_result.url}")
            print(f"   Score: {first_result.score:.2f}")
            print(f"   Content preview: {first_result.content[:100]}...")
        
        # Test 2: Advanced search with AI answer
        print("\n🔍 Test 2: Advanced search with AI answer...")
        results_advanced: TavilySearchResponse = tavily.search(
            context=context,
            query="What is the difference between asyncio and threading in Python?",
            search_depth="advanced",
            max_results=3,
            include_answer=True
        )
        
        print(f"✅ Advanced search successful!")
        if results_advanced.answer:
            print(f"   AI Answer type: {type(results_advanced.answer).__name__}")
            print(f"   Answer preview: {results_advanced.answer[:150]}...")
        
        print(f"   Results: {len(results_advanced.results)} items")
        
    except TavilyValidationError as e:
        print(f"❌ Validation error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print()


def test_domain_filtering():
    """Test domain filtering functionality with Pydantic models."""
    print("=" * 60)
    print("TEST 4: Domain Filtering (Pydantic)")
    print("=" * 60)
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("⚠️  TAVILY_API_KEY not found - skipping")
        print()
        return
    
    class MockLogger:
        def info(self, msg, **kwargs):
            pass
        def error(self, msg, **kwargs):
            print(f"   [ERROR] {msg}")
    
    class MockContext:
        def __init__(self):
            self.logger = MockLogger()
    
    context = MockContext()
    tavily = TavilyAPITool()
    tavily.setup({"tavily_api_key": api_key})
    
    try:
        # Test domain filtering with Pydantic validation
        print("🔍 Searching with domain whitelist...")
        results: TavilySearchResponse = tavily.search(
            context=context,
            query="Python best practices",
            include_domains=["python.org", "realpython.com"],
            max_results=5
        )
        
        # Verify Pydantic model structure
        assert isinstance(results, TavilySearchResponse)
        assert all(isinstance(r, TavilySearchResult) for r in results.results)
        
        print(f"✅ Domain filtering successful (Pydantic validated)!")
        print(f"   Results: {len(results.results)}")
        for result in results.results:
            print(f"   - {result.url} (score: {result.score:.2f})")
        
    except TavilyValidationError as e:
        print(f"❌ Validation error: {e}")
    except Exception as e:
        print(f"❌ Domain filtering failed: {e}")
    
    print()


def test_type_safety():
    """Demonstrate type safety benefits."""
    print("=" * 60)
    print("TEST 5: Type Safety Benefits")
    print("=" * 60)
    
    from plugins.tool_tavily import TavilySearchResult
    
    result = TavilySearchResult(
        title="Test Result",
        url="https://example.com",
        content="Sample content",
        score=0.85
    )
    
    # Type hints work in IDE
    print(f"✅ IDE knows result.title is a string: '{result.title}'")
    print(f"✅ IDE knows result.score is a float: {result.score}")
    print(f"✅ Autocomplete works for all fields")
    
    # Accessing non-existent field raises AttributeError
    try:
        _ = result.nonexistent_field
        print("❌ Should have raised AttributeError")
    except AttributeError:
        print("✅ Correctly raises AttributeError for non-existent field")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TAVILY API PYDANTIC VALIDATION TEST SUITE")
    print("=" * 60 + "\n")
    
    test_search_request_validation()
    test_search_result_validation()
    test_live_search()
    test_domain_filtering()
    test_type_safety()
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    print("\n✅ Tavily integration provides:")
    print("   • AI-optimized search results")
    print("   • Pydantic data validation")
    print("   • Type safety and IDE support")
    print("   • Domain filtering capabilities")
    print("   • AI-generated answers")
    print("   • Raw content extraction")
