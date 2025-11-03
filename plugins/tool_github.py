"""
GitHub Integration Plugin
Enables Sophie to autonomously improve herself by creating PRs, managing issues, and interacting with repositories.

Created: 2025-11-03
Purpose: Self-improvement and autonomous development workflow
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import os
import requests
import logging

logger = logging.getLogger(__name__)


# Custom exceptions
class GitHubError(Exception):
    """Base exception for GitHub errors"""
    pass


class GitHubAuthenticationError(GitHubError):
    """Raised when GitHub authentication fails"""
    pass


class GitHubValidationError(GitHubError):
    """Raised when input validation fails"""
    pass


class GitHubAPIError(GitHubError):
    """Raised for GitHub API errors"""
    pass


# Request Models (Input Validation)
class CreateIssueRequest(BaseModel):
    """Request model for creating a GitHub issue"""
    owner: str = Field(..., min_length=1, description="Repository owner")
    repo: str = Field(..., min_length=1, description="Repository name")
    title: str = Field(..., min_length=1, max_length=256, description="Issue title")
    body: str = Field(..., description="Issue body/description")
    labels: Optional[List[str]] = Field(default=None, description="Issue labels")
    assignees: Optional[List[str]] = Field(default=None, description="Issue assignees")


class ListIssuesRequest(BaseModel):
    """Request model for listing GitHub issues"""
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    state: str = Field(default="open", pattern="^(open|closed|all)$")
    labels: Optional[str] = Field(default=None, description="Comma-separated label names")
    sort: str = Field(default="created", pattern="^(created|updated|comments)$")
    direction: str = Field(default="desc", pattern="^(asc|desc)$")
    per_page: int = Field(default=30, ge=1, le=100)


class UpdateIssueRequest(BaseModel):
    """Request model for updating a GitHub issue"""
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    issue_number: int = Field(..., ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    body: Optional[str] = Field(None)
    state: Optional[str] = Field(None, pattern="^(open|closed)$")
    labels: Optional[List[str]] = Field(None)


class AddCommentRequest(BaseModel):
    """Request model for adding a comment to an issue"""
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    issue_number: int = Field(..., ge=1)
    body: str = Field(..., min_length=1, description="Comment text")


class CreatePullRequestRequest(BaseModel):
    """Request model for creating a pull request"""
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(..., description="PR description")
    head: str = Field(..., min_length=1, description="Branch containing changes")
    base: str = Field(default="master", description="Branch to merge into")
    draft: bool = Field(default=False, description="Create as draft PR")


class MergePullRequestRequest(BaseModel):
    """Request model for merging a pull request"""
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)
    pull_number: int = Field(..., ge=1)
    commit_title: Optional[str] = Field(None)
    commit_message: Optional[str] = Field(None)
    merge_method: str = Field(default="merge", pattern="^(merge|squash|rebase)$")


# Response Models
class IssueResponse(BaseModel):
    """Response model for GitHub issue"""
    number: int
    title: str
    body: str
    state: str
    html_url: str
    created_at: str
    updated_at: str
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)


class PullRequestResponse(BaseModel):
    """Response model for GitHub pull request"""
    number: int
    title: str
    body: str
    state: str
    html_url: str
    head: str  # Branch with changes
    base: str  # Target branch
    created_at: str
    updated_at: str
    mergeable: Optional[bool] = None
    merged: bool = False


class CommentResponse(BaseModel):
    """Response model for GitHub comment"""
    id: int
    body: str
    html_url: str
    created_at: str
    updated_at: str


class ToolGitHub(BasePlugin):
    """
    GitHub Integration Plugin
    
    Provides comprehensive GitHub API access for Sophie to autonomously
    manage her own development through issues, PRs, and repository operations.
    """
    
    @property
    def name(self) -> str:
        return "tool_github"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.base_url = "https://api.github.com"
        self.session = None
    
    def setup(self, config: dict) -> None:
        """
        Sets up the GitHub API client with authentication.

        Args:
            config: A dictionary containing the configuration for the plugin.
                   Expected keys: 'github_token' or uses GITHUB_TOKEN env var
        """
        # Get API token from config or environment
        token_config = config.get("github_token", "")
        
        # If config contains ${ENV_VAR}, load from environment
        if token_config.startswith("${") and token_config.endswith("}"):
            env_var_name = token_config[2:-1]
            self.api_key = os.getenv(env_var_name, "")
        else:
            self.api_key = token_config or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PAT")

        if not self.api_key:
            logger.warning(
                "GitHub token is not configured. GitHub API will not be available. "
                "Set GITHUB_TOKEN or GITHUB_PAT environment variable."
            )
        else:
            # Initialize session with headers
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"token {self.api_key}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Sophia-AI-Agent"
            })
            logger.info("GitHub API client initialized successfully")

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Makes an authenticated request to the GitHub API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "repos/owner/repo/issues")
            data: Optional request body data
            
        Returns:
            Dict with API response
            
        Raises:
            GitHubAuthenticationError: If authentication fails
            GitHubAPIError: If API request fails
        """
        if not self.api_key:
            raise GitHubAuthenticationError("GitHub API token is not configured.")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, params=data)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PATCH":
                response = self.session.patch(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise GitHubAuthenticationError("GitHub API authentication failed. Check your token.")
            
            # Handle rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                if response.headers['X-RateLimit-Remaining'] == '0':
                    raise GitHubAPIError("GitHub API rate limit exceeded.")
            
            response.raise_for_status()
            
            # Some endpoints return 204 No Content
            if response.status_code == 204:
                return {}
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            raise GitHubAPIError(f"HTTP error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            raise GitHubAPIError(f"Request failed: {str(e)}")

    def create_issue(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> IssueResponse:
        """
        Creates a new GitHub issue.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: Optional list of label names
            assignees: Optional list of GitHub usernames to assign
            
        Returns:
            IssueResponse with created issue details
        """
        # Validate input
        try:
            request = CreateIssueRequest(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                labels=labels,
                assignees=assignees
            )
        except Exception as e:
            context.logger.error(f"Invalid create_issue parameters: {e}")
            raise GitHubValidationError(f"Invalid parameters: {e}")
        
        # Prepare request data
        data = {
            "title": request.title,
            "body": request.body
        }
        if request.labels:
            data["labels"] = request.labels
        if request.assignees:
            data["assignees"] = request.assignees
        
        # Make API request
        context.logger.info(f"Creating issue in {owner}/{repo}: {title}")
        response = self._make_request("POST", f"repos/{owner}/{repo}/issues", data)
        
        # Parse response
        return IssueResponse(
            number=response["number"],
            title=response["title"],
            body=response["body"],
            state=response["state"],
            html_url=response["html_url"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            labels=[label["name"] for label in response.get("labels", [])],
            assignees=[user["login"] for user in response.get("assignees", [])]
        )

    def list_issues(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30
    ) -> List[IssueResponse]:
        """
        Lists issues from a GitHub repository.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            state: Filter by state: open, closed, all
            labels: Comma-separated label names
            sort: Sort by: created, updated, comments
            direction: Sort direction: asc, desc
            per_page: Results per page (1-100)
            
        Returns:
            List of IssueResponse objects
        """
        # Validate input
        try:
            request = ListIssuesRequest(
                owner=owner,
                repo=repo,
                state=state,
                labels=labels,
                sort=sort,
                direction=direction,
                per_page=per_page
            )
        except Exception as e:
            context.logger.error(f"Invalid list_issues parameters: {e}")
            raise GitHubValidationError(f"Invalid parameters: {e}")
        
        # Prepare query parameters
        params = {
            "state": request.state,
            "sort": request.sort,
            "direction": request.direction,
            "per_page": request.per_page
        }
        if request.labels:
            params["labels"] = request.labels
        
        # Make API request
        context.logger.info(f"Listing issues from {owner}/{repo}")
        response = self._make_request("GET", f"repos/{owner}/{repo}/issues", params)
        
        # Parse response
        issues = []
        for issue_data in response:
            # Skip pull requests (they appear in issues endpoint)
            if "pull_request" in issue_data:
                continue
                
            issues.append(IssueResponse(
                number=issue_data["number"],
                title=issue_data["title"],
                body=issue_data.get("body", ""),
                state=issue_data["state"],
                html_url=issue_data["html_url"],
                created_at=issue_data["created_at"],
                updated_at=issue_data["updated_at"],
                labels=[label["name"] for label in issue_data.get("labels", [])],
                assignees=[user["login"] for user in issue_data.get("assignees", [])]
            ))
        
        return issues

    def update_issue(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> IssueResponse:
        """
        Updates an existing GitHub issue.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number to update
            title: New title (optional)
            body: New body (optional)
            state: New state: open or closed (optional)
            labels: New labels list (optional)
            
        Returns:
            IssueResponse with updated issue details
        """
        # Validate input
        try:
            request = UpdateIssueRequest(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                title=title,
                body=body,
                state=state,
                labels=labels
            )
        except Exception as e:
            context.logger.error(f"Invalid update_issue parameters: {e}")
            raise GitHubValidationError(f"Invalid parameters: {e}")
        
        # Prepare request data (only include provided fields)
        data = {}
        if request.title:
            data["title"] = request.title
        if request.body is not None:
            data["body"] = request.body
        if request.state:
            data["state"] = request.state
        if request.labels is not None:
            data["labels"] = request.labels
        
        # Make API request
        context.logger.info(f"Updating issue #{issue_number} in {owner}/{repo}")
        response = self._make_request("PATCH", f"repos/{owner}/{repo}/issues/{issue_number}", data)
        
        # Parse response
        return IssueResponse(
            number=response["number"],
            title=response["title"],
            body=response.get("body", ""),
            state=response["state"],
            html_url=response["html_url"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            labels=[label["name"] for label in response.get("labels", [])],
            assignees=[user["login"] for user in response.get("assignees", [])]
        )

    def close_issue(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        issue_number: int
    ) -> IssueResponse:
        """
        Closes a GitHub issue.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number to close
            
        Returns:
            IssueResponse with closed issue details
        """
        return self.update_issue(context, owner, repo, issue_number, state="closed")

    def add_comment(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        issue_number: int,
        body: str
    ) -> CommentResponse:
        """
        Adds a comment to a GitHub issue or pull request.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            issue_number: Issue/PR number
            body: Comment text
            
        Returns:
            CommentResponse with created comment details
        """
        # Validate input
        try:
            request = AddCommentRequest(
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                body=body
            )
        except Exception as e:
            context.logger.error(f"Invalid add_comment parameters: {e}")
            raise GitHubValidationError(f"Invalid parameters: {e}")
        
        # Make API request
        context.logger.info(f"Adding comment to #{issue_number} in {owner}/{repo}")
        response = self._make_request(
            "POST",
            f"repos/{owner}/{repo}/issues/{issue_number}/comments",
            {"body": request.body}
        )
        
        # Parse response
        return CommentResponse(
            id=response["id"],
            body=response["body"],
            html_url=response["html_url"],
            created_at=response["created_at"],
            updated_at=response["updated_at"]
        )

    def create_pull_request(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "master",
        draft: bool = False
    ) -> PullRequestResponse:
        """
        Creates a new pull request.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Branch containing changes
            base: Branch to merge into (default: master)
            draft: Create as draft PR
            
        Returns:
            PullRequestResponse with created PR details
        """
        # Validate input
        try:
            request = CreatePullRequestRequest(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft
            )
        except Exception as e:
            context.logger.error(f"Invalid create_pull_request parameters: {e}")
            raise GitHubValidationError(f"Invalid parameters: {e}")
        
        # Prepare request data
        data = {
            "title": request.title,
            "body": request.body,
            "head": request.head,
            "base": request.base,
            "draft": request.draft
        }
        
        # Make API request
        context.logger.info(f"Creating PR in {owner}/{repo}: {head} -> {base}")
        response = self._make_request("POST", f"repos/{owner}/{repo}/pulls", data)
        
        # Parse response
        return PullRequestResponse(
            number=response["number"],
            title=response["title"],
            body=response.get("body", ""),
            state=response["state"],
            html_url=response["html_url"],
            head=response["head"]["ref"],
            base=response["base"]["ref"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            mergeable=response.get("mergeable"),
            merged=response.get("merged", False)
        )

    def merge_pull_request(
        self,
        context: SharedContext,
        owner: str,
        repo: str,
        pull_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Merges a pull request.
        
        Args:
            context: Shared context for the session
            owner: Repository owner
            repo: Repository name
            pull_number: PR number to merge
            commit_title: Optional commit title
            commit_message: Optional commit message
            merge_method: Method: merge, squash, or rebase
            
        Returns:
            Dict with merge result
        """
        # Validate input
        try:
            request = MergePullRequestRequest(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                commit_title=commit_title,
                commit_message=commit_message,
                merge_method=merge_method
            )
        except Exception as e:
            context.logger.error(f"Invalid merge_pull_request parameters: {e}")
            raise GitHubValidationError(f"Invalid parameters: {e}")
        
        # Prepare request data
        data = {
            "merge_method": request.merge_method
        }
        if request.commit_title:
            data["commit_title"] = request.commit_title
        if request.commit_message:
            data["commit_message"] = request.commit_message
        
        # Make API request
        context.logger.info(f"Merging PR #{pull_number} in {owner}/{repo}")
        response = self._make_request("PUT", f"repos/{owner}/{repo}/pulls/{pull_number}/merge", data)
        
        return response

    async def execute(self, context: SharedContext, method_name: str, **kwargs) -> Any:
        """
        Executes a tool method dynamically.
        
        Args:
            context: The shared context for the session
            method_name: Name of the method to execute
            **kwargs: Method arguments
            
        Returns:
            Method execution result
        """
        if not hasattr(self, method_name):
            raise ValueError(f"Unknown method: {method_name}")
        
        method = getattr(self, method_name)
        return method(context, **kwargs)

    def get_tool_definitions(self) -> List[dict]:
        """
        Returns the tool definitions for this plugin.
        
        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "name": "create_issue",
                "description": "Create a new GitHub issue",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "title": "Issue title (string, required)",
                    "body": "Issue description (string, required)",
                    "labels": "List of label names (list of strings, optional)",
                    "assignees": "List of GitHub usernames to assign (list of strings, optional)"
                }
            },
            {
                "name": "list_issues",
                "description": "List issues from a GitHub repository",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "state": "Filter by state: open, closed, all (string, default: open)",
                    "labels": "Comma-separated label names (string, optional)",
                    "sort": "Sort by: created, updated, comments (string, default: created)",
                    "direction": "Sort direction: asc, desc (string, default: desc)",
                    "per_page": "Results per page, 1-100 (integer, default: 30)"
                }
            },
            {
                "name": "update_issue",
                "description": "Update an existing GitHub issue",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "issue_number": "Issue number (integer, required)",
                    "title": "New title (string, optional)",
                    "body": "New description (string, optional)",
                    "state": "New state: open or closed (string, optional)",
                    "labels": "New labels list (list of strings, optional)"
                }
            },
            {
                "name": "close_issue",
                "description": "Close a GitHub issue",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "issue_number": "Issue number to close (integer, required)"
                }
            },
            {
                "name": "add_comment",
                "description": "Add a comment to a GitHub issue or pull request",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "issue_number": "Issue or PR number (integer, required)",
                    "body": "Comment text (string, required)"
                }
            },
            {
                "name": "create_pull_request",
                "description": "Create a new pull request",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "title": "PR title (string, required)",
                    "body": "PR description (string, required)",
                    "head": "Branch containing changes (string, required)",
                    "base": "Branch to merge into (string, default: master)",
                    "draft": "Create as draft PR (boolean, default: false)"
                }
            },
            {
                "name": "merge_pull_request",
                "description": "Merge a pull request",
                "parameters": {
                    "owner": "Repository owner (string, required)",
                    "repo": "Repository name (string, required)",
                    "pull_number": "PR number to merge (integer, required)",
                    "commit_title": "Commit title (string, optional)",
                    "commit_message": "Commit message (string, optional)",
                    "merge_method": "Method: merge, squash, or rebase (string, default: merge)"
                }
            }
        ]
