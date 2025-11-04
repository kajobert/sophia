# Jules API - Complete Documentation

**Source:** Google for Developers (developers.google.com/jules/api)  
**Date:** November 2, 2025  
**API Version:** v1alpha  
**Base URL:** https://jules.googleapis.com/v1alpha

---

## 🎯 Overview

Jules API is Google's AI-powered coding assistant API that can:
- Create complete applications from prompts
- Modify existing code via natural language
- Work with GitHub repositories
- Create pull requests automatically

## ⚠️ API Limits & Quotas

**IMPORTANT:** Jules API has strict usage limits:

- **Daily Task Limit:** 100 sessions per day
- **Counter:** Resets at midnight UTC
- **Recommendation:** Track your usage carefully to avoid hitting limits
- **Best Practice:** Batch related tasks when possible

**Usage Tracking:**
- Each `create()` call creates a new session and counts toward the limit
- `get()` and `list()` calls do NOT count toward the limit
- Monitor your daily usage to stay within quota

---

## 🔑 Authentication

**Method:** API Key via HTTP Header

```bash
X-Goog-Api-Key: YOUR_API_KEY
```

**Example:**
```bash
curl 'https://jules.googleapis.com/v1alpha/sessions' \
  -H 'X-Goog-Api-Key: YOUR_API_KEY'
```

---

## 📚 REST Resources

### 1. **v1alpha.sessions**

Create and manage coding sessions.

#### Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create` | `POST /v1alpha/sessions` | Creates a new session |
| `get` | `GET /v1alpha/{name=sessions/*}` | Gets a single session |
| `list` | `GET /v1alpha/sessions` | Lists all sessions |

#### Create Session Example:

```bash
curl 'https://jules.googleapis.com/v1alpha/sessions' \
  -X POST \
  -H "Content-Type: application/json" \
  -H 'X-Goog-Api-Key: YOUR_API_KEY' \
  -d '{
    "prompt": "Create a boba app!",
    "sourceContext": {
      "source": "sources/github/bobalover/boba",
      "githubRepoContext": {
        "startingBranch": "main"
      }
    },
    "automationMode": "AUTO_CREATE_PR",
    "title": "Boba App"
  }'
```

**Request Body:**
```json
{
  "prompt": "string",          // Task description
  "sourceContext": {
    "source": "string",        // Format: "sources/github/{owner}/{repo}"
    "githubRepoContext": {
      "startingBranch": "string"
    }
  },
  "automationMode": "string",  // "AUTO_CREATE_PR" or manual
  "title": "string"            // Session title
}
```

**Response:**
```json
{
  "name": "sessions/{session_id}",
  "state": "ACTIVE",
  "activities": []
}
```

---

### 2. **v1alpha.sessions.activities**

Get information about activities within a session.

#### Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get` | `GET /v1alpha/{name=sessions/*/activities/*}` | Gets a single activity |

---

### 3. **v1alpha.sources**

Manage source repositories.

#### Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `list` | `GET /v1alpha/sources` | Lists available sources |

#### List Sources Example:

```bash
curl 'https://jules.googleapis.com/v1alpha/sources' \
  -H 'X-Goog-Api-Key: YOUR_API_KEY'
```

---

## 💬 Send Message to Session

Continue a conversation in an existing session.

```bash
curl 'https://jules.googleapis.com/v1alpha/sessions/{SESSION_ID}:sendMessage' \
  -X POST \
  -H "Content-Type: application/json" \
  -H 'X-Goog-Api-Key: YOUR_API_KEY' \
  -d '{
    "prompt": "Can you make the app corgi themed?"
  }'
```

---

## 🔄 Typical Workflow

### 1. List Available Sources
```bash
GET /v1alpha/sources
```

### 2. Create a Session
```bash
POST /v1alpha/sessions
{
  "prompt": "Your task",
  "sourceContext": { ... },
  "title": "Session Name"
}
```

### 3. Send Follow-up Messages
```bash
POST /v1alpha/sessions/{SESSION_ID}:sendMessage
{
  "prompt": "Follow-up instruction"
}
```

### 4. Check Session Status
```bash
GET /v1alpha/sessions/{SESSION_ID}
```

### 5. Get Activity Details
```bash
GET /v1alpha/sessions/{SESSION_ID}/activities/{ACTIVITY_ID}
```

---

## 🛡️ Error Handling

**Common HTTP Status Codes:**

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Verify API key |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check resource ID |
| 429 | Rate Limited | Implement backoff |
| 500 | Server Error | Retry with backoff |

---

## 📦 Python Integration Example

```python
import requests

class JulesAPI:
    BASE_URL = "https://jules.googleapis.com/v1alpha"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key
        }
    
    def list_sources(self) -> dict:
        """List available sources."""
        response = requests.get(
            f"{self.BASE_URL}/sources",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_session(self, prompt: str, source: str, 
                      branch: str = "main", 
                      title: str = "",
                      auto_pr: bool = False) -> dict:
        """Create a new Jules session."""
        data = {
            "prompt": prompt,
            "sourceContext": {
                "source": source,
                "githubRepoContext": {
                    "startingBranch": branch
                }
            },
            "title": title
        }
        
        if auto_pr:
            data["automationMode"] = "AUTO_CREATE_PR"
        
        response = requests.post(
            f"{self.BASE_URL}/sessions",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def send_message(self, session_id: str, prompt: str) -> dict:
        """Send a message to an existing session."""
        response = requests.post(
            f"{self.BASE_URL}/sessions/{session_id}:sendMessage",
            headers=self.headers,
            json={"prompt": prompt}
        )
        response.raise_for_status()
        return response.json()
    
    def get_session(self, session_id: str) -> dict:
        """Get session details."""
        response = requests.get(
            f"{self.BASE_URL}/sessions/{session_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_sessions(self) -> dict:
        """List all sessions."""
        response = requests.get(
            f"{self.BASE_URL}/sessions",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

---

## 🚀 Use Cases

### 1. Create New Feature
```python
jules = JulesAPI(api_key="YOUR_KEY")
session = jules.create_session(
    prompt="Add dark mode support to the app",
    source="sources/github/myorg/myapp",
    title="Dark Mode Implementation",
    auto_pr=True
)
```

### 2. Fix Bug
```python
session = jules.create_session(
    prompt="Fix the login page crashing on mobile",
    source="sources/github/myorg/myapp",
    branch="develop"
)

# Follow up
jules.send_message(
    session["name"].split("/")[1],
    "Also add error logging"
)
```

### 3. Refactor Code
```python
session = jules.create_session(
    prompt="Refactor authentication to use JWT tokens",
    source="sources/github/myorg/myapp",
    title="Auth Refactoring"
)
```

---

## 📋 Best Practices

1. **Use Descriptive Prompts**
   - Be specific about what you want
   - Include context and requirements
   - Mention files or components if relevant

2. **Check Session State**
   - Monitor session progress
   - Handle different states (ACTIVE, COMPLETED, FAILED)

3. **Error Handling**
   - Implement retry logic for transient errors
   - Validate API key before requests
   - Handle rate limits gracefully

4. **Source Context**
   - Ensure GitHub repo is accessible
   - Use correct branch names
   - Verify source format: `sources/github/{owner}/{repo}`

5. **Automation Mode**
   - Use `AUTO_CREATE_PR` for autonomous operation
   - Manual mode for review-before-commit workflows

---

## 🔗 Official Resources

- **API Reference:** https://developers.google.com/jules/api/reference/rest
- **Quickstart:** https://developers.google.com/jules/api
- **Blog Post:** https://developers.googleblog.com/en/level-up-your-dev-game-the-jules-api-is-here/

---

## ⚠️ Important Notes

- **Alpha Version:** API is in v1alpha, expect changes
- **API Key Required:** Get from Google Cloud Console
- **GitHub Integration:** Requires GitHub OAuth setup
- **Rate Limits:** Check documentation for current limits
- **Pricing:** Check Google Cloud pricing for current rates

---

**Last Updated:** November 2, 2025  
**Documentation Status:** Complete and ready for plugin implementation
