"""
Models API routes.

Endpoints for querying available LLM models.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("", response_model=Dict[str, Any])
async def get_models():
    """
    Get available LLM models with metadata.
    
    Returns:
        Dictionary containing:
        - List of available models
        - Model configurations
        - Pricing information (if available)
        - Current/default model
        - Model aliases
    
    Example:
        ```
        GET /api/v1/models
        
        Response:
        {
            "models": [
                {
                    "name": "gemini-2.0-flash-exp",
                    "provider": "gemini",
                    "config": {"temperature": 0.7, "max_output_tokens": 8192},
                    "pricing": null,
                    "available": true
                },
                {
                    "name": "qwen/qwen-2.5-72b-instruct",
                    "provider": "openrouter",
                    "config": {"temperature": 0.7, "max_tokens": 8000},
                    "pricing": {"prompt": 0.07, "completion": 0.26},
                    "available": true
                }
            ],
            "total": 15,
            "current_model": "gemini-2.0-flash-exp",
            "aliases": {
                "powerful": "gemini-2.0-flash-exp",
                "cheap": "qwen/qwen-2.5-72b-instruct",
                "balanced": "google/gemma-3-27b-it"
            }
        }
        ```
    """
    try:
        return orchestrator_manager.get_models()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get models: {str(e)}"
        )
