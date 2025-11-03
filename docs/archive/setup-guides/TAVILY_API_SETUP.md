# Tavily API Setup Guide

## Overview

Tavily AI Search API provides optimized search results specifically designed for AI applications. This plugin integrates Tavily into Sophia V2 with full Pydantic validation.

## Features

- ✅ **AI-Optimized Search**: Results ranked by relevance for AI consumption
- ✅ **AI-Generated Answers**: Optional direct answers to queries
- ✅ **Deep Search**: Basic (fast) or Advanced (thorough) search modes
- ✅ **Domain Filtering**: Whitelist/blacklist specific domains
- ✅ **Raw Content Extraction**: Get full page content
- ✅ **Image Search**: Find related images
- ✅ **Pydantic Validation**: Type-safe, validated responses
- ✅ **Environment Variable Support**: Secure API key management

## Quick Start

### 1. Get API Key

1. Visit [https://tavily.com](https://tavily.com)
2. Sign up for free account
3. Get your API key from dashboard
4. Free tier includes generous monthly quota

### 2. Configure API Key

Add your Tavily API key to `.env` file:

```bash
# In /workspaces/sophia/.env
TAVILY_API_KEY=tvly-your-api-key-here
```

**IMPORTANT**: Never commit the `.env` file to Git! It's already in `.gitignore`.

### 3. Update Configuration

The plugin is already configured in `config/settings.yaml`:

```yaml
plugins:
  tool_tavily:
    tavily_api_key: "${TAVILY_API_KEY}"  # Loaded from .env
```

### 4. Verify Installation

Run the test suite:

```bash
cd /workspaces/sophia
source .venv/bin/activate
export TAVILY_API_KEY="your-key-here"
PYTHONPATH=/workspaces/sophia python scripts/test_tavily.py
```

All 5 tests should pass ✅

## Available Methods

### 1. `search()` - AI-Optimized Web Search

Performs intelligent web search with optional AI-generated answers.

**Parameters:**
- `query` (str, required): Search query
- `search_depth` (str): "basic" (fast) or "advanced" (thorough)
- `max_results` (int): 1-20 results (default: 5)
- `include_answer` (bool): Get AI-generated answer (default: False)
- `include_raw_content` (bool): Include full page content (default: False)
- `include_images` (bool): Include related images (default: False)
- `include_domains` (List[str]): Whitelist domains
- `exclude_domains` (List[str]): Blacklist domains

**Returns:** `TavilySearchResponse` (Pydantic model)

**Example:**
```python
from plugins.tool_tavily import TavilyAPITool

tavily = TavilyAPITool()
tavily.setup({"tavily_api_key": "your-key"})

results = tavily.search(
    context=context,
    query="Python async programming best practices",
    search_depth="advanced",
    max_results=10,
    include_answer=True
)

# Type-safe access
print(results.answer)  # AI-generated answer
for result in results.results:
    print(f"{result.title}: {result.url} (score: {result.score})")
```

### 2. `extract()` - Content Extraction

Extracts clean content from URLs.

**Parameters:**
- `urls` (List[str], required): List of URLs to extract

**Returns:** Dict with extracted content

**Example:**
```python
content = tavily.extract(
    context=context,
    urls=["https://example.com/article1", "https://example.com/article2"]
)
```

## Pydantic Models

### TavilySearchRequest
Input validation for search parameters.

```python
class TavilySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    search_depth: str = Field(default="basic", pattern="^(basic|advanced)$")
    max_results: int = Field(default=5, ge=1, le=20)
    include_answer: bool = Field(default=False)
    include_raw_content: bool = Field(default=False)
    include_images: bool = Field(default=False)
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
```

### TavilySearchResult
Single search result with validation.

```python
class TavilySearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float  # 0.0-1.0
    raw_content: Optional[str] = None
```

### TavilySearchResponse
Complete search response.

```python
class TavilySearchResponse(BaseModel):
    query: str
    results: List[TavilySearchResult]
    answer: Optional[str] = None
    images: Optional[List[str]] = None
    response_time: Optional[float] = None
```

## Error Handling

The plugin provides three custom exceptions:

```python
from plugins.tool_tavily import (
    TavilyAPIError,           # Base exception
    TavilyAuthenticationError,# 401/403 errors
    TavilyValidationError,    # Pydantic validation failures
    TavilyRateLimitError      # 429 rate limit exceeded
)

try:
    results = tavily.search(context, query="test")
except TavilyValidationError as e:
    print(f"Invalid parameters: {e}")
except TavilyAuthenticationError as e:
    print(f"API key issue: {e}")
except TavilyRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except TavilyAPIError as e:
    print(f"API error: {e}")
```

## Sophie Integration

Sophie's planner automatically discovers Tavily methods:

```bash
python run.py "Use Tavily to search for 'Python async programming' and summarize the results"
```

Sophie will:
1. Detect the tool_tavily plugin
2. Call the `search()` method
3. Receive type-safe `TavilySearchResponse`
4. Process results with full Pydantic validation

## Testing

### Run All Tests
```bash
PYTHONPATH=/workspaces/sophia python scripts/test_tavily.py
```

### Run Integration Test
```bash
PYTHONPATH=/workspaces/sophia python scripts/test_sophie_tavily_integration.py
```

### Expected Output
```
✅ TEST 1: TavilySearchRequest Validation - PASSED
✅ TEST 2: TavilySearchResult Validation - PASSED
✅ TEST 3: Live Tavily API Integration - PASSED
✅ TEST 4: Domain Filtering (Pydantic) - PASSED
✅ TEST 5: Type Safety Benefits - PASSED
```

## Best Practices

1. **Use search_depth wisely**:
   - `"basic"` for quick queries (faster, cheaper)
   - `"advanced"` for complex research (slower, more thorough)

2. **Request AI answers when needed**:
   ```python
   results = tavily.search(query="...", include_answer=True)
   if results.answer:
       print(results.answer)  # Direct answer to question
   ```

3. **Filter domains for quality**:
   ```python
   results = tavily.search(
       query="Python docs",
       include_domains=["python.org", "docs.python.org"]
   )
   ```

4. **Check scores**:
   ```python
   for result in results.results:
       if result.score > 0.9:  # High relevance
           process_result(result)
   ```

## Security Notes

- ✅ API key stored in `.env` (not committed to Git)
- ✅ Environment variable syntax `${TAVILY_API_KEY}` in config
- ✅ Plugin validates API key presence before requests
- ✅ Clear error messages for authentication failures

## Troubleshooting

### "TAVILY_API_KEY not configured"
- Check `.env` file exists
- Verify key is set: `echo $TAVILY_API_KEY`
- Restart application after adding key

### "Invalid API key"
- Verify key is correct (check Tavily dashboard)
- Ensure no extra spaces or quotes in `.env`

### "Rate limit exceeded"
- Free tier has monthly limits
- Wait or upgrade to paid plan
- Implement caching for repeated queries

## API Limits

**Free Tier:**
- 1,000 searches/month
- Basic + Advanced search modes
- All features included

**Paid Tiers:**
- Higher limits
- Priority support
- See [tavily.com/pricing](https://tavily.com/pricing)

## Resources

- **Official Docs**: https://docs.tavily.com
- **API Reference**: https://docs.tavily.com/api-reference
- **Dashboard**: https://app.tavily.com
- **Pricing**: https://tavily.com/pricing

---

**Author:** GitHub Copilot  
**Date:** 2025-11-02  
**Version:** 1.0.0  
**Plugin:** tool_tavily.py
