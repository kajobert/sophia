from pathlib import Path
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.operation_metadata import OperationMetadata
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, Boolean, MetaData, insert, select, and_
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class SQLiteMemory(BasePlugin):
    """A memory plugin that stores conversation history in a SQLite database."""

    @property
    def name(self) -> str:
        return "memory_sqlite"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.MEMORY

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initializes the database connection and creates the table if it doesn't exist."""
        db_path_str = config.get("db_path", "data/memory/sophia_memory.db")

        # Ensure the directory for the database exists
        db_path = Path(db_path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path_str}")
        self.metadata = MetaData()
        
        # Conversation history table
        self.history_table = Table(
            "conversation_history",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("session_id", String),
            Column("role", String),
            Column("content", String),
            Column("operation_metadata", String),  # JSON-serialized OperationMetadata
        )
        
        # Operation tracking table (for self-improvement and offline dreaming)
        self.operation_tracking_table = Table(
            "operation_tracking",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("operation_id", String, unique=True, nullable=False),
            Column("session_id", String),
            Column("timestamp", String, nullable=False),
            Column("model_used", String, nullable=False),
            Column("model_type", String, nullable=False),
            Column("operation_type", String, nullable=False),
            Column("offline_mode", Boolean, nullable=False, default=False),
            Column("success", Boolean, nullable=False, default=True),
            Column("quality_score", Float),
            Column("evaluated_at", String),
            Column("evaluation_model", String),
            Column("prompt_tokens", Integer),
            Column("completion_tokens", Integer),
            Column("total_tokens", Integer),
            Column("latency_ms", Float),
            Column("error_message", String),
            Column("raw_metadata", String),  # Full JSON for extensibility
        )
        
        self.metadata.create_all(self.engine)
        logger.info(f"SQLite memory initialized: {db_path_str}")

    async def execute(self, context: SharedContext) -> SharedContext:
        """Saves the current user input and LLM response to the database."""
        user_input = context.user_input
        llm_response = context.payload.get("llm_response")

        if not user_input or not llm_response:
            return context

        with self.engine.connect() as conn:
            conn.execute(
                insert(self.history_table).values(
                    session_id=context.session_id, role="user", content=user_input
                )
            )
            conn.execute(
                insert(self.history_table).values(
                    session_id=context.session_id, role="assistant", content=llm_response
                )
            )
            conn.commit()
            context.logger.info(
                "Saved interaction to short-term memory.",
                extra={"plugin_name": self.name},
            )

        return context

    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieves the most recent history for a session."""
        with self.engine.connect() as conn:
            stmt = (
                select(self.history_table.c.role, self.history_table.c.content)
                .where(self.history_table.c.session_id == session_id)
                .order_by(self.history_table.c.id.desc())
                .limit(limit)
            )
            results = conn.execute(stmt).fetchall()
            return [{"role": row[0], "content": row[1]} for row in reversed(results)]
    
    # ===== OPERATION TRACKING METHODS (NEW) =====
    
    def save_operation(self, metadata: OperationMetadata) -> None:
        """
        Save operation metadata to tracking table.
        
        Args:
            metadata: OperationMetadata instance to store
        """
        with self.engine.connect() as conn:
            conn.execute(
                insert(self.operation_tracking_table).values(
                    operation_id=metadata.operation_id,
                    session_id=metadata.session_id,
                    timestamp=metadata.timestamp,
                    model_used=metadata.model_used,
                    model_type=metadata.model_type,
                    operation_type=metadata.operation_type,
                    offline_mode=metadata.offline_mode,
                    success=metadata.success,
                    quality_score=metadata.quality_score,
                    evaluated_at=metadata.evaluated_at,
                    evaluation_model=metadata.evaluation_model,
                    prompt_tokens=metadata.prompt_tokens,
                    completion_tokens=metadata.completion_tokens,
                    total_tokens=metadata.total_tokens,
                    latency_ms=metadata.latency_ms,
                    error_message=metadata.error_message,
                    raw_metadata=metadata.to_json(),
                )
            )
            conn.commit()
            logger.debug(f"Saved operation {metadata.operation_id} to tracking table")
    
    def get_unevaluated_offline_operations(self, limit: Optional[int] = None) -> List[OperationMetadata]:
        """
        Get all offline operations that haven't been evaluated yet.
        
        Args:
            limit: Maximum number of operations to return (None = all)
        
        Returns:
            List of OperationMetadata instances
        """
        with self.engine.connect() as conn:
            stmt = (
                select(self.operation_tracking_table)
                .where(
                    and_(
                        self.operation_tracking_table.c.offline_mode == True,
                        self.operation_tracking_table.c.quality_score == None
                    )
                )
                .order_by(self.operation_tracking_table.c.timestamp.desc())
            )
            
            if limit:
                stmt = stmt.limit(limit)
            
            results = conn.execute(stmt).fetchall()
            
            # Convert to OperationMetadata instances
            operations = []
            for row in results:
                metadata = OperationMetadata.from_json(row[-1])  # raw_metadata is last column
                operations.append(metadata)
            
            logger.info(f"Found {len(operations)} unevaluated offline operations")
            return operations
    
    def update_operation_quality(
        self,
        operation_id: str,
        quality_score: float,
        evaluation_model: str,
        evaluated_at: str
    ) -> None:
        """
        Update operation with quality evaluation results.
        
        Args:
            operation_id: Operation identifier
            quality_score: Quality score (0.0-1.0)
            evaluation_model: Model used for evaluation
            evaluated_at: Timestamp of evaluation
        """
        from sqlalchemy import update
        
        with self.engine.connect() as conn:
            stmt = (
                update(self.operation_tracking_table)
                .where(self.operation_tracking_table.c.operation_id == operation_id)
                .values(
                    quality_score=quality_score,
                    evaluation_model=evaluation_model,
                    evaluated_at=evaluated_at
                )
            )
            conn.execute(stmt)
            conn.commit()
            logger.debug(f"Updated operation {operation_id} with quality score {quality_score:.2f}")
    
    def get_operation_statistics(self, days: int = 7) -> Dict:
        """
        Get statistics about operations over the last N days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with statistics
        """
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self.engine.connect() as conn:
            # Total operations
            stmt = select(self.operation_tracking_table).where(
                self.operation_tracking_table.c.timestamp >= cutoff_date
            )
            all_ops = conn.execute(stmt).fetchall()
            
            total_count = len(all_ops)
            offline_count = sum(1 for op in all_ops if op[7])  # offline_mode column
            online_count = total_count - offline_count
            
            # Quality scores
            offline_scores = [op[9] for op in all_ops if op[7] and op[9] is not None]  # quality_score
            online_scores = [op[9] for op in all_ops if not op[7] and op[9] is not None]
            
            stats = {
                "days_analyzed": days,
                "total_operations": total_count,
                "offline_operations": offline_count,
                "online_operations": online_count,
                "offline_percentage": (offline_count / total_count * 100) if total_count > 0 else 0,
                "offline_avg_quality": sum(offline_scores) / len(offline_scores) if offline_scores else None,
                "online_avg_quality": sum(online_scores) / len(online_scores) if online_scores else None,
                "quality_gap": None
            }
            
            if stats["offline_avg_quality"] and stats["online_avg_quality"]:
                stats["quality_gap"] = stats["online_avg_quality"] - stats["offline_avg_quality"]
            
            return stats
