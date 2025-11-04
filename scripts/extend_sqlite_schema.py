#!/usr/bin/env python3
"""
Extend SQLite schema to support operation tracking with model signatures.

This script:
1. Creates operation_tracking table
2. Adds operation_metadata column to conversation_history
3. Creates indexes for efficient querying
4. Preserves existing data

Run: python scripts/extend_sqlite_schema.py
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "data/memory/sophia_memory.db"


def extend_schema():
    """Extend SQLite schema with operation tracking."""
    # Ensure DB directory exists
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if operation_tracking table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='operation_tracking'
        """)
        if cursor.fetchone():
            logger.info("✅ operation_tracking table already exists")
        else:
            # Create operation_tracking table
            logger.info("📊 Creating operation_tracking table...")
            cursor.execute("""
                CREATE TABLE operation_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT UNIQUE NOT NULL,
                    session_id TEXT,
                    timestamp TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    offline_mode BOOLEAN NOT NULL DEFAULT 0,
                    success BOOLEAN NOT NULL DEFAULT 1,
                    quality_score REAL,
                    evaluated_at TEXT,
                    evaluation_model TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    latency_ms REAL,
                    error_message TEXT,
                    raw_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ operation_tracking table created")
        
        # Create indexes
        logger.info("🔍 Creating indexes...")
        
        # Index for finding unevaluated offline operations
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_offline_unevaluated 
            ON operation_tracking(offline_mode, quality_score)
            WHERE offline_mode = 1 AND quality_score IS NULL
        """)
        
        # Index for session-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON operation_tracking(session_id)
        """)
        
        # Index for timestamp-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON operation_tracking(timestamp DESC)
        """)
        
        # Index for model performance analysis
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_quality 
            ON operation_tracking(model_used, quality_score)
        """)
        
        logger.info("✅ Indexes created")
        
        # Check if conversation_history has operation_metadata column
        cursor.execute("PRAGMA table_info(conversation_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "operation_metadata" not in columns:
            logger.info("📝 Adding operation_metadata column to conversation_history...")
            cursor.execute("""
                ALTER TABLE conversation_history 
                ADD COLUMN operation_metadata TEXT
            """)
            logger.info("✅ operation_metadata column added")
        else:
            logger.info("✅ operation_metadata column already exists")
        
        conn.commit()
        logger.info("✅ Schema extension completed successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Tables: {', '.join(tables)}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Schema extension failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info("🚀 Starting SQLite schema extension...")
    extend_schema()
    logger.info("✨ Done!")
