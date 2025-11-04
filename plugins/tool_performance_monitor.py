"""
Performance monitoring plugin for tracking LLM calls, tool usage and session metrics.
Created by Sophie (AI Agent) on 2025-11-02 based on research of AI agent best practices.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import sqlite3
from pydantic import BaseModel, Field
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class LogLLMCallRequest(BaseModel):
    """Request model for logging LLM calls"""

    model: str = Field(..., min_length=1, description="LLM model name")
    input_tokens: int = Field(..., ge=0, description="Input tokens used")
    output_tokens: int = Field(..., ge=0, description="Output tokens generated")
    cost: float = Field(..., ge=0.0, description="Cost in USD")


class LogToolUsageRequest(BaseModel):
    """Request model for logging tool usage"""

    tool_name: str = Field(..., min_length=1, description="Name of the tool")
    method_name: str = Field(..., min_length=1, description="Method called")
    success: bool = Field(..., description="Whether the call succeeded")


class GetMetricsRequest(BaseModel):
    """Request model for getting metrics"""

    time_period: str = Field(
        default="24h", pattern="^(1h|24h|7d|30d)$", description="Time period for metrics"
    )


class LLMCall(BaseModel):
    """Internal model for LLM API call data"""

    timestamp: datetime
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost: float = Field(ge=0.0)


class ToolUsage(BaseModel):
    """Internal model for tool usage data"""

    timestamp: datetime
    tool_name: str
    method_name: str
    success: bool


class Metrics(BaseModel):
    """Response model for aggregated metrics"""

    total_llm_calls: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    total_cost: float = Field(ge=0.0)
    tool_usage_count: Dict[str, int]
    success_rate: float = Field(ge=0.0, le=1.0)
    timespan: str


class ToolPerformanceMonitor(BasePlugin):
    """Performance monitoring plugin for tracking system metrics"""

    def __init__(self):
        """Initialize the performance monitor"""
        super().__init__()
        self.db_path = "data/performance_metrics.db"
        self._init_db()

    @property
    def name(self) -> str:
        return "tool_performance_monitor"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Setup the plugin"""
        self.db_path = config.get("db_path", "data/performance_metrics.db")
        self._init_db()

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
                    "name": "log_llm_call",
                    "description": "Log an LLM API call with token usage and cost",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model": {"type": "string", "description": "LLM model name"},
                            "input_tokens": {
                                "type": "integer",
                                "description": "Input tokens used",
                            },
                            "output_tokens": {
                                "type": "integer",
                                "description": "Output tokens generated",
                            },
                            "cost": {"type": "number", "description": "Cost in USD"},
                        },
                        "required": ["model", "input_tokens", "output_tokens", "cost"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "log_tool_usage",
                    "description": "Log a tool usage event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "description": "Name of the tool"},
                            "method_name": {"type": "string", "description": "Method called"},
                            "success": {
                                "type": "boolean",
                                "description": "Whether call succeeded",
                            },
                        },
                        "required": ["tool_name", "method_name", "success"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_metrics",
                    "description": "Get aggregated performance metrics",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_period": {
                                "type": "string",
                                "description": "Time period for metrics",
                                "enum": ["1h", "24h", "7d", "30d"],
                                "default": "24h",
                            }
                        },
                        "required": [],
                    },
                },
            },
        ]

    def _init_db(self):
        """Initialize SQLite database and tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create LLM calls table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_calls (
                timestamp DATETIME,
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL
            )
        """
        )

        # Create tool usage table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_usage (
                timestamp DATETIME,
                tool_name TEXT,
                method_name TEXT,
                success INTEGER
            )
        """
        )

        conn.commit()
        conn.close()

    def log_llm_call(
        self,
        context: SharedContext,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> str:
        """
        Log an LLM API call with Pydantic validation.

        Args:
            context: Shared context for logging
            model: LLM model name (e.g., "claude-3-5-sonnet-20241022")
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            cost: Cost in USD

        Returns:
            Success message string

        Raises:
            ValidationError: If parameters are invalid

        Example:
            >>> result = monitor.log_llm_call(
            ...     context=context,
            ...     model="claude-3-5-sonnet-20241022",
            ...     input_tokens=1000,
            ...     output_tokens=500,
            ...     cost=0.015
            ... )
        """
        # Validate input using Pydantic
        try:
            request = LogLLMCallRequest(
                model=model, input_tokens=input_tokens, output_tokens=output_tokens, cost=cost
            )
        except Exception as e:
            context.logger.error(
                f"Invalid LLM call parameters: {e}", extra={"plugin_name": self.name}
            )
            raise

        # Create internal model with timestamp
        call = LLMCall(
            timestamp=datetime.now(),
            model=request.model,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            cost=request.cost,
        )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO llm_calls (timestamp, model, input_tokens, output_tokens, cost)
            VALUES (?, ?, ?, ?, ?)
        """,
            (call.timestamp, call.model, call.input_tokens, call.output_tokens, call.cost),
        )

        conn.commit()
        conn.close()

        context.logger.info(
            f"Logged LLM call: {model}, {input_tokens + output_tokens} tokens, ${cost:.4f}",
            extra={"plugin_name": self.name},
        )

        return f"Logged LLM call for {model}"

    def log_tool_usage(
        self, context: SharedContext, tool_name: str, method_name: str, success: bool
    ) -> str:
        """
        Log a tool usage event with Pydantic validation.

        Args:
            context: Shared context for logging
            tool_name: Name of the tool (e.g., "tool_tavily")
            method_name: Method called (e.g., "search")
            success: Whether the call succeeded

        Returns:
            Success message string

        Raises:
            ValidationError: If parameters are invalid

        Example:
            >>> result = monitor.log_tool_usage(
            ...     context=context,
            ...     tool_name="tool_tavily",
            ...     method_name="search",
            ...     success=True
            ... )
        """
        # Validate input using Pydantic
        try:
            request = LogToolUsageRequest(
                tool_name=tool_name, method_name=method_name, success=success
            )
        except Exception as e:
            context.logger.error(
                f"Invalid tool usage parameters: {e}", extra={"plugin_name": self.name}
            )
            raise

        # Create internal model with timestamp
        usage = ToolUsage(
            timestamp=datetime.now(),
            tool_name=request.tool_name,
            method_name=request.method_name,
            success=request.success,
        )

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO tool_usage (timestamp, tool_name, method_name, success)
            VALUES (?, ?, ?, ?)
        """,
            (usage.timestamp, usage.tool_name, usage.method_name, int(usage.success)),
        )

        conn.commit()
        conn.close()

        context.logger.info(
            f"Logged tool usage: {tool_name}.{method_name} ({'success' if success else 'failed'})",
            extra={"plugin_name": self.name},
        )

        return f"Logged tool usage for {tool_name}.{method_name}"

    def get_metrics(self, context: SharedContext, time_period: str = "24h") -> Metrics:
        """
        Get aggregated performance metrics with Pydantic validation.

        Args:
            context: Shared context for logging
            time_period: Time period for metrics ("1h", "24h", "7d", "30d")

        Returns:
            Metrics model with aggregated data

        Raises:
            ValidationError: If time_period is invalid

        Example:
            >>> metrics = monitor.get_metrics(context, "24h")
            >>> print(f"Total cost: ${metrics.total_cost:.4f}")
            >>> print(f"Success rate: {metrics.success_rate*100:.1f}%")
        """
        # Validate input using Pydantic
        try:
            request = GetMetricsRequest(time_period=time_period)
        except Exception as e:
            context.logger.error(f"Invalid time_period: {e}", extra={"plugin_name": self.name})
            raise

        # Convert time period to timedelta
        period_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        delta = period_map[request.time_period]
        start_time = datetime.now() - delta

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get LLM metrics
        c.execute(
            """
            SELECT COUNT(*), SUM(input_tokens + output_tokens), SUM(cost)
            FROM llm_calls 
            WHERE timestamp > ?
        """,
            (start_time,),
        )
        result = c.fetchone()
        llm_calls = result[0] if result[0] else 0
        total_tokens = result[1] if result[1] else 0
        total_cost = result[2] if result[2] else 0.0

        # Get tool usage metrics
        c.execute(
            """
            SELECT tool_name, COUNT(*) 
            FROM tool_usage 
            WHERE timestamp > ?
            GROUP BY tool_name
        """,
            (start_time,),
        )
        tool_usage = dict(c.fetchall())

        # Get success rate
        c.execute(
            """
            SELECT AVG(CAST(success AS FLOAT))
            FROM tool_usage 
            WHERE timestamp > ?
        """,
            (start_time,),
        )
        result = c.fetchone()
        success_rate = result[0] if result[0] else 0.0

        conn.close()

        # Return validated Pydantic model
        metrics = Metrics(
            total_llm_calls=llm_calls,
            total_tokens=total_tokens,
            total_cost=total_cost,
            tool_usage_count=tool_usage,
            success_rate=success_rate,
            timespan=request.time_period,
        )

        context.logger.info(
            f"Retrieved metrics for {time_period}: {llm_calls} LLM calls, ${total_cost:.4f} cost",
            extra={"plugin_name": self.name},
        )

        return metrics
