"""
Operation Metadata Module

Tracks which LLM performed each operation for self-improvement and offline dreaming.

Usage:
    from core.operation_metadata import OperationMetadata, track_operation
    
    # Create metadata
    metadata = OperationMetadata.create(
        model_used="llama3.1:8b",
        operation_type="planning",
        offline_mode=True
    )
    
    # Mark success/failure
    metadata.mark_success(prompt_tokens=150, completion_tokens=80, latency_ms=2500)
    # OR
    metadata.mark_failure("Connection timeout")
    
    # Store in database
    await memory_plugin.save_operation(metadata)
"""

import uuid
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json

logger = logging.getLogger(__name__)


@dataclass
class OperationMetadata:
    """
    Metadata tracking which LLM performed an operation.
    
    Used for:
    - Offline dreaming (track local vs cloud LLM usage)
    - Self-evaluation (quality scoring of offline operations)
    - Performance monitoring (latency, token usage)
    - Self-improvement (learn from evaluations)
    """
    
    # Identifiers
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Model information
    model_used: str = ""  # e.g., "llama3.1:8b" or "openrouter/deepseek/deepseek-chat"
    model_type: str = ""  # "local" or "cloud"
    
    # Operation details
    operation_type: str = ""  # "planning" | "execution" | "consolidation" | "response"
    offline_mode: bool = False  # True if network was unavailable
    
    # Execution results
    success: bool = False
    error_message: Optional[str] = None
    
    # Performance metrics
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    
    # Self-evaluation (filled later when online)
    quality_score: Optional[float] = None  # 0.0-1.0
    evaluated_at: Optional[str] = None
    evaluation_model: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        model_used: str,
        operation_type: str,
        offline_mode: bool = False,
        session_id: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> "OperationMetadata":
        """
        Create new operation metadata.
        
        Args:
            model_used: Name of the LLM model (e.g., "llama3.1:8b")
            operation_type: Type of operation (planning, execution, etc.)
            offline_mode: Whether network is unavailable
            session_id: Session identifier
            model_type: "local" or "cloud" (auto-detected if None)
        
        Returns:
            OperationMetadata instance
        """
        # Auto-detect model type if not provided
        if model_type is None:
            if "llama" in model_used.lower() or "gemma" in model_used.lower():
                model_type = "local"
            else:
                model_type = "cloud"
        
        return cls(
            model_used=model_used,
            model_type=model_type,
            operation_type=operation_type,
            offline_mode=offline_mode,
            session_id=session_id,
        )
    
    def mark_success(
        self,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        """
        Mark operation as successful and record metrics.
        
        Args:
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion
            latency_ms: Response time in milliseconds
        """
        self.success = True
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = (
            (prompt_tokens or 0) + (completion_tokens or 0) if prompt_tokens or completion_tokens else None
        )
        self.latency_ms = latency_ms
        
        logger.debug(
            f"Operation {self.operation_id} marked successful "
            f"(model={self.model_used}, tokens={self.total_tokens}, latency={latency_ms}ms)"
        )
    
    def mark_failure(self, error_message: str) -> None:
        """
        Mark operation as failed.
        
        Args:
            error_message: Description of the error
        """
        self.success = False
        self.error_message = error_message
        
        logger.warning(
            f"Operation {self.operation_id} marked failed: {error_message} "
            f"(model={self.model_used})"
        )
    
    def set_quality_score(
        self,
        quality_score: float,
        evaluation_model: str,
    ) -> None:
        """
        Record quality evaluation score.
        
        Args:
            quality_score: Quality score from 0.0 (poor) to 1.0 (excellent)
            evaluation_model: Model used for evaluation
        """
        if not 0.0 <= quality_score <= 1.0:
            raise ValueError(f"Quality score must be 0.0-1.0, got {quality_score}")
        
        self.quality_score = quality_score
        self.evaluated_at = datetime.now().isoformat()
        self.evaluation_model = evaluation_model
        
        logger.info(
            f"Operation {self.operation_id} evaluated: quality={quality_score:.2f} "
            f"by {evaluation_model}"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "OperationMetadata":
        """Create from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "OperationMetadata":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def __repr__(self) -> str:
        return (
            f"OperationMetadata("
            f"id={self.operation_id[:8]}..., "
            f"model={self.model_used}, "
            f"type={self.operation_type}, "
            f"offline={self.offline_mode}, "
            f"success={self.success}, "
            f"quality={self.quality_score or 'N/A'}"
            f")"
        )


# Convenience function for quick tracking
def track_operation(
    model_used: str,
    operation_type: str,
    offline_mode: bool = False,
    session_id: Optional[str] = None,
) -> OperationMetadata:
    """
    Quick helper to create operation metadata.
    
    Args:
        model_used: Name of the LLM model
        operation_type: Type of operation
        offline_mode: Whether network is unavailable
        session_id: Session identifier
    
    Returns:
        OperationMetadata instance
    
    Example:
        metadata = track_operation("llama3.1:8b", "planning", offline_mode=True)
        try:
            # ... perform operation ...
            metadata.mark_success(prompt_tokens=150, completion_tokens=80)
        except Exception as e:
            metadata.mark_failure(str(e))
    """
    return OperationMetadata.create(
        model_used=model_used,
        operation_type=operation_type,
        offline_mode=offline_mode,
        session_id=session_id,
    )
