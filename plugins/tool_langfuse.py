"""
Langfuse Observability Integration Plugin
Provides end-to-end tracing and debugging for AI agents.

Created based on Sophie's research on 2025-11-02.
Implements trace visualization, error analytics, and performance metrics.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import os
import logging

logger = logging.getLogger(__name__)


# Custom exceptions
class LangfuseError(Exception):
    """Base exception for Langfuse errors"""
    pass


class LangfuseAuthenticationError(LangfuseError):
    """Raised when API authentication fails"""
    pass


class LangfuseValidationError(LangfuseError):
    """Raised when request validation fails"""
    pass


class LangfuseAPIError(LangfuseError):
    """Raised when API request fails"""
    pass


# ============================================================================
# Request Models (Input Validation)
# ============================================================================

class TraceGenerationRequest(BaseModel):
    """Request model for creating a trace with generation"""
    name: str = Field(..., min_length=1, description="Name of the trace")
    input_text: str = Field(..., description="Input text for the generation")
    output_text: Optional[str] = Field(None, description="Output text from the generation")
    model: Optional[str] = Field(None, description="Model name used")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class SpanRequest(BaseModel):
    """Request model for creating a span within a trace"""
    trace_id: str = Field(..., min_length=1, description="ID of the parent trace")
    name: str = Field(..., min_length=1, description="Name of the span")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data for the span")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data from the span")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class EventRequest(BaseModel):
    """Request model for logging an event"""
    trace_id: str = Field(..., min_length=1, description="ID of the parent trace")
    name: str = Field(..., min_length=1, description="Name of the event")
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$", description="Event level")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event metadata")


class ScoreRequest(BaseModel):
    """Request model for adding a score/evaluation"""
    trace_id: str = Field(..., min_length=1, description="ID of the trace to score")
    name: str = Field(..., min_length=1, description="Name of the score metric")
    value: float = Field(..., description="Score value")
    comment: Optional[str] = Field(None, description="Optional comment about the score")


# ============================================================================
# Response Models (Output Validation)
# ============================================================================

class LangfuseTrace(BaseModel):
    """Model for Langfuse trace response"""
    id: str
    name: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LangfuseGeneration(BaseModel):
    """Model for Langfuse generation response"""
    id: str
    trace_id: str
    name: str
    model: Optional[str] = None
    input_text: str
    output_text: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    cost: Optional[float] = None


class LangfuseSpan(BaseModel):
    """Model for Langfuse span response"""
    id: str
    trace_id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LangfuseMetrics(BaseModel):
    """Model for aggregated metrics"""
    total_traces: int = Field(ge=0)
    total_generations: int = Field(ge=0)
    total_cost: float = Field(ge=0.0)
    average_latency: float = Field(ge=0.0)
    error_rate: float = Field(ge=0.0, le=1.0)


# ============================================================================
# Main Plugin
# ============================================================================

class ToolLangfuse(BasePlugin):
    """
    Langfuse Observability Integration Plugin
    
    Provides comprehensive tracing, debugging, and performance monitoring
    for AI agents using Langfuse's open-source platform.
    
    Features:
    - Trace visualization (decision trees, tool calls, LLM interactions)
    - Error analytics (classification, frequency, root cause)
    - Performance metrics (latency, cost per step)
    - Multi-agent workflow support
    """

    def __init__(self):
        """Initialize the Langfuse plugin"""
        super().__init__()
        self.api_key = None
        self.secret_key = None
        self.host = "https://cloud.langfuse.com"
        self.client = None

    @property
    def name(self) -> str:
        return "tool_langfuse"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """
        Setup the Langfuse plugin with configuration.
        
        Args:
            config: Configuration dictionary with optional keys:
                - api_key: Langfuse API key (or use LANGFUSE_PUBLIC_KEY env var)
                - secret_key: Langfuse secret key (or use LANGFUSE_SECRET_KEY env var)
                - host: Langfuse host URL (default: https://cloud.langfuse.com)
        """
        # Get credentials from config or environment
        self.api_key = config.get("api_key") or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = config.get("secret_key") or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = config.get("host", "https://cloud.langfuse.com")
        
        # Allow lazy initialization - credentials can be set later
        if not self.api_key or not self.secret_key:
            logger.warning(
                "Langfuse credentials not found. Plugin will be available but methods will fail "
                "until LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set."
            )
        
        # Initialize Langfuse client
        try:
            from langfuse import Langfuse
            self.client = Langfuse(
                public_key=self.api_key,
                secret_key=self.secret_key,
                host=self.host
            )
        except ImportError:
            raise LangfuseError(
                "Langfuse SDK not installed. Install with: pip install langfuse"
            )
        except Exception as e:
            raise LangfuseAuthenticationError(f"Failed to initialize Langfuse client: {e}")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This tool is not directly executed in the main loop.
        Its methods are called by cognitive plugins.
        """
        return context

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for the planner"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_trace",
                    "description": "Create a new trace for tracking AI agent execution. Use this to start monitoring a workflow.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the trace (e.g., 'user_query_processing')"
                            },
                            "input_text": {
                                "type": "string",
                                "description": "Input text for the trace"
                            },
                            "output_text": {
                                "type": "string",
                                "description": "Output text (optional, can be added later)"
                            },
                            "model": {
                                "type": "string",
                                "description": "Model name used (optional)"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata (optional)",
                                "default": {}
                            }
                        },
                        "required": ["name", "input_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_span",
                    "description": "Create a span within a trace to track a specific operation (tool call, LLM request, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trace_id": {
                                "type": "string",
                                "description": "ID of the parent trace"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the span (e.g., 'tavily_search', 'llm_call')"
                            },
                            "input_data": {
                                "type": "object",
                                "description": "Input data for the span (optional)"
                            },
                            "output_data": {
                                "type": "object",
                                "description": "Output data from the span (optional)"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata (optional)",
                                "default": {}
                            }
                        },
                        "required": ["trace_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "log_event",
                    "description": "Log an event within a trace (for debugging, errors, warnings)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trace_id": {
                                "type": "string",
                                "description": "ID of the parent trace"
                            },
                            "name": {
                                "type": "string",
                                "description": "Event name"
                            },
                            "level": {
                                "type": "string",
                                "description": "Event level",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                                "default": "INFO"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Event metadata (optional)",
                                "default": {}
                            }
                        },
                        "required": ["trace_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_score",
                    "description": "Add a score/evaluation to a trace (quality, accuracy, user feedback)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trace_id": {
                                "type": "string",
                                "description": "ID of the trace to score"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the score metric (e.g., 'accuracy', 'user_rating')"
                            },
                            "value": {
                                "type": "number",
                                "description": "Score value"
                            },
                            "comment": {
                                "type": "string",
                                "description": "Optional comment about the score"
                            }
                        },
                        "required": ["trace_id", "name", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_traces",
                    "description": "Retrieve traces for analysis and debugging",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of traces to retrieve",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def create_trace(
        self,
        context: SharedContext,
        name: str,
        input_text: str,
        output_text: Optional[str] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LangfuseTrace:
        """
        Create a new Langfuse trace with Pydantic validation.
        
        Args:
            context: Shared context for logging
            name: Name of the trace
            input_text: Input text for the trace
            output_text: Output text (optional)
            model: Model name (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            LangfuseTrace with validated trace data
            
        Raises:
            LangfuseValidationError: If parameters are invalid
            LangfuseAPIError: If API request fails
            
        Example:
            >>> trace = langfuse.create_trace(
            ...     context=context,
            ...     name="user_query",
            ...     input_text="What is 2+2?",
            ...     metadata={"user_id": "123"}
            ... )
            >>> trace_id = trace.id
        """
        # Validate input using Pydantic
        try:
            request = TraceGenerationRequest(
                name=name,
                input_text=input_text,
                output_text=output_text,
                model=model,
                metadata=metadata or {}
            )
        except Exception as e:
            context.logger.error(
                f"Invalid trace parameters: {e}",
                extra={"plugin_name": self.name}
            )
            raise LangfuseValidationError(f"Invalid trace parameters: {e}")
        
        # Create trace via Langfuse SDK
        try:
            trace = self.client.trace(
                name=request.name,
                input=request.input_text,
                output=request.output_text,
                metadata=request.metadata,
                session_id=context.session_id
            )
            
            # Return validated response
            result = LangfuseTrace(
                id=trace.id,
                name=request.name,
                timestamp=datetime.now(),
                session_id=context.session_id,
                metadata=request.metadata
            )
            
            context.logger.info(
                f"Created Langfuse trace: {result.id} ({name})",
                extra={"plugin_name": self.name}
            )
            
            return result
            
        except Exception as e:
            context.logger.error(
                f"Failed to create Langfuse trace: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            raise LangfuseAPIError(f"Failed to create trace: {e}")

    def create_span(
        self,
        context: SharedContext,
        trace_id: str,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LangfuseSpan:
        """
        Create a span within a trace with Pydantic validation.
        
        Args:
            context: Shared context for logging
            trace_id: ID of the parent trace
            name: Name of the span
            input_data: Input data for the span (optional)
            output_data: Output data from the span (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            LangfuseSpan with validated span data
            
        Raises:
            LangfuseValidationError: If parameters are invalid
            LangfuseAPIError: If API request fails
            
        Example:
            >>> span = langfuse.create_span(
            ...     context=context,
            ...     trace_id=trace.id,
            ...     name="tavily_search",
            ...     input_data={"query": "AI agents"},
            ...     output_data={"results": 5}
            ... )
        """
        # Validate input using Pydantic
        try:
            request = SpanRequest(
                trace_id=trace_id,
                name=name,
                input_data=input_data,
                output_data=output_data,
                metadata=metadata or {}
            )
        except Exception as e:
            context.logger.error(
                f"Invalid span parameters: {e}",
                extra={"plugin_name": self.name}
            )
            raise LangfuseValidationError(f"Invalid span parameters: {e}")
        
        # Create span via Langfuse SDK
        try:
            span = self.client.span(
                trace_id=request.trace_id,
                name=request.name,
                input=request.input_data,
                output=request.output_data,
                metadata=request.metadata
            )
            
            # Return validated response
            result = LangfuseSpan(
                id=span.id,
                trace_id=request.trace_id,
                name=request.name,
                start_time=datetime.now(),
                input_data=request.input_data,
                output_data=request.output_data,
                metadata=request.metadata
            )
            
            context.logger.info(
                f"Created Langfuse span: {result.id} ({name}) in trace {trace_id}",
                extra={"plugin_name": self.name}
            )
            
            return result
            
        except Exception as e:
            context.logger.error(
                f"Failed to create Langfuse span: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            raise LangfuseAPIError(f"Failed to create span: {e}")

    def log_event(
        self,
        context: SharedContext,
        trace_id: str,
        name: str,
        level: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an event within a trace with Pydantic validation.
        
        Args:
            context: Shared context for logging
            trace_id: ID of the parent trace
            name: Event name
            level: Event level (DEBUG, INFO, WARNING, ERROR)
            metadata: Event metadata (optional)
            
        Returns:
            Success message string
            
        Raises:
            LangfuseValidationError: If parameters are invalid
            LangfuseAPIError: If API request fails
            
        Example:
            >>> langfuse.log_event(
            ...     context=context,
            ...     trace_id=trace.id,
            ...     name="tool_error",
            ...     level="ERROR",
            ...     metadata={"error": "Connection timeout"}
            ... )
        """
        # Validate input using Pydantic
        try:
            request = EventRequest(
                trace_id=trace_id,
                name=name,
                level=level,
                metadata=metadata or {}
            )
        except Exception as e:
            context.logger.error(
                f"Invalid event parameters: {e}",
                extra={"plugin_name": self.name}
            )
            raise LangfuseValidationError(f"Invalid event parameters: {e}")
        
        # Log event via Langfuse SDK
        try:
            self.client.event(
                trace_id=request.trace_id,
                name=request.name,
                level=request.level,
                metadata=request.metadata
            )
            
            context.logger.info(
                f"Logged {level} event '{name}' to trace {trace_id}",
                extra={"plugin_name": self.name}
            )
            
            return f"Logged event '{name}' ({level}) to trace {trace_id}"
            
        except Exception as e:
            context.logger.error(
                f"Failed to log Langfuse event: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            raise LangfuseAPIError(f"Failed to log event: {e}")

    def add_score(
        self,
        context: SharedContext,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None
    ) -> str:
        """
        Add a score/evaluation to a trace with Pydantic validation.
        
        Args:
            context: Shared context for logging
            trace_id: ID of the trace to score
            name: Name of the score metric
            value: Score value
            comment: Optional comment about the score
            
        Returns:
            Success message string
            
        Raises:
            LangfuseValidationError: If parameters are invalid
            LangfuseAPIError: If API request fails
            
        Example:
            >>> langfuse.add_score(
            ...     context=context,
            ...     trace_id=trace.id,
            ...     name="accuracy",
            ...     value=0.95,
            ...     comment="High quality response"
            ... )
        """
        # Validate input using Pydantic
        try:
            request = ScoreRequest(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment
            )
        except Exception as e:
            context.logger.error(
                f"Invalid score parameters: {e}",
                extra={"plugin_name": self.name}
            )
            raise LangfuseValidationError(f"Invalid score parameters: {e}")
        
        # Add score via Langfuse SDK
        try:
            self.client.score(
                trace_id=request.trace_id,
                name=request.name,
                value=request.value,
                comment=request.comment
            )
            
            context.logger.info(
                f"Added score '{name}' ({value}) to trace {trace_id}",
                extra={"plugin_name": self.name}
            )
            
            return f"Added score '{name}' ({value}) to trace {trace_id}"
            
        except Exception as e:
            context.logger.error(
                f"Failed to add Langfuse score: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            raise LangfuseAPIError(f"Failed to add score: {e}")

    def get_traces(
        self,
        context: SharedContext,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve traces for analysis and debugging.
        
        Args:
            context: Shared context for logging
            limit: Maximum number of traces to retrieve
            
        Returns:
            List of trace dictionaries
            
        Raises:
            LangfuseAPIError: If API request fails
            
        Example:
            >>> traces = langfuse.get_traces(context, limit=5)
            >>> for trace in traces:
            ...     print(f"{trace['id']}: {trace['name']}")
        """
        try:
            # Fetch traces from Langfuse
            traces = self.client.fetch_traces(limit=limit)
            
            result = [
                {
                    "id": trace.id,
                    "name": trace.name,
                    "timestamp": trace.timestamp,
                    "session_id": trace.session_id,
                    "metadata": trace.metadata
                }
                for trace in traces.data
            ]
            
            context.logger.info(
                f"Retrieved {len(result)} traces from Langfuse",
                extra={"plugin_name": self.name}
            )
            
            return result
            
        except Exception as e:
            context.logger.error(
                f"Failed to retrieve Langfuse traces: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            raise LangfuseAPIError(f"Failed to retrieve traces: {e}")
