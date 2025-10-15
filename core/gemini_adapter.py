"""
GeminiAdapter: Direct adapter for Google Gemini API (2.5 Flash).

This adapter provides native Gemini integration for NomadOrchestratorV2,
bypassing OpenRouter for direct API access with better control and features.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai package is required for GeminiAdapter. "
        "Install with: pip install google-generativeai"
    )


class GeminiAdapter:
    """
    Direct adapter for Google Gemini API.
    
    Features:
    - Async/sync support
    - Token usage tracking
    - Gemini 2.5 Flash optimization
    - Safety settings control
    - Structured output support (JSON mode)
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40,
        **kwargs
    ):
        """
        Initialize Gemini adapter.
        
        Args:
            model_name: Gemini model name (default: gemini-2.0-flash-exp)
            api_key: Gemini API key (if None, loads from GEMINI_API_KEY env var)
            temperature: Sampling temperature (0.0-2.0)
            max_output_tokens: Maximum tokens in response
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
        """
        # Load API key
        load_dotenv()
        final_api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not final_api_key:
            raise ValueError(
                "GEMINI_API_KEY must be provided either as argument or environment variable. "
                "Create .env file with: GEMINI_API_KEY='your_key_here'"
            )
        
        # Configure Gemini
        genai.configure(api_key=final_api_key)
        
        # Store config
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.top_p = top_p
        self.top_k = top_k
        
        # Initialize model
        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k,
            ),
            # Safety settings (permissive for development)
            safety_settings={
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            }
        )
        
        # Token tracking
        self._last_usage = {}
    
    async def generate_content_async(
        self,
        prompt: str,
        **kwargs
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate content asynchronously.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
        
        Returns:
            Tuple of (response_text, usage_dict)
            
        Example:
            response, usage = await adapter.generate_content_async("Hello!")
            print(f"Response: {response}")
            print(f"Tokens: {usage['usage']['total_tokens']}")
        """
        # Override generation config if provided
        generation_config = {}
        if "temperature" in kwargs:
            generation_config["temperature"] = kwargs.pop("temperature")
        if "max_output_tokens" in kwargs:
            generation_config["max_output_tokens"] = kwargs.pop("max_output_tokens")
        
        # Generate in thread pool (Gemini SDK is sync)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._model.generate_content(
                prompt,
                generation_config=generation_config if generation_config else None
            )
        )
        
        # Extract usage metadata
        usage_metadata = {}
        if hasattr(response, 'usage_metadata'):
            metadata = response.usage_metadata
            usage_metadata = {
                "usage": {
                    "prompt_tokens": getattr(metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(metadata, 'total_token_count', 0),
                }
            }
        
        self._last_usage = usage_metadata
        
        # Extract text
        try:
            response_text = response.text
        except ValueError as e:
            # Handle blocked responses
            if hasattr(response, 'prompt_feedback'):
                response_text = f"[Response blocked: {response.prompt_feedback}]"
            else:
                response_text = f"[Error: {e}]"
        except Exception as e:
            response_text = f"[Unexpected error: {e}]"
        
        return response_text, usage_metadata
    
    def generate_content(
        self,
        prompt: str,
        **kwargs
    ) -> tuple[str, Dict[str, Any]]:
        """
        Synchronous wrapper for generate_content_async.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
        
        Returns:
            Tuple of (response_text, usage_dict)
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, run in new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    self.generate_content_async(prompt, **kwargs)
                ).result()
        else:
            return loop.run_until_complete(
                self.generate_content_async(prompt, **kwargs)
            )
    
    def get_last_usage(self) -> Dict[str, Any]:
        """
        Get token usage from last API call.
        
        Returns:
            Dict with usage statistics
        """
        return self._last_usage
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximate).
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Approximate token count
        """
        try:
            result = self._model.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Fallback: rough estimate (4 chars per token)
            return len(text) // 4
    
    def __repr__(self) -> str:
        return f"GeminiAdapter(model={self.model_name}, temp={self.temperature})"


# Convenience function for quick testing
async def test_gemini():
    """Quick test function."""
    adapter = GeminiAdapter()
    response, usage = await adapter.generate_content_async("Say 'Hello from Gemini 2.5 Flash!'")
    print(f"Response: {response}")
    print(f"Tokens: {usage['usage']['total_tokens']}")


if __name__ == "__main__":
    # Test the adapter
    asyncio.run(test_gemini())
