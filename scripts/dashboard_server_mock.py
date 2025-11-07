"""Standalone Dashboard Server with MOCK DATA

For E2E testing without full Sophia kernel.
Jules can run this in his VM to test dashboard frontend.

Usage:
    python scripts/dashboard_server_mock.py
    
Then run Playwright tests:
    pytest tests/e2e/test_dashboard.py

Access:
    http://127.0.0.1:8000/dashboard
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from uvicorn import Config, Server

# ============================================
# MOCK DATA GENERATORS
# ============================================

def generate_mock_tasks(count=20):
    """Generate mock tasks for testing."""
    statuses = ["pending", "in_progress", "completed", "failed"]
    priorities = ["low", "medium", "high", "critical"]
    
    tasks = []
    for i in range(count):
        created = datetime.now() - timedelta(hours=random.randint(1, 48))
        tasks.append({
            "id": i + 1,
            "description": f"Mock task {i+1}: Test dashboard functionality",
            "status": random.choice(statuses),
            "priority": random.choice(priorities),
            "created_at": created.isoformat(),
            "updated_at": created.isoformat(),
            "assigned_plugin": random.choice(["cognitive_planner", "tool_web_search", "cognitive_memory"]),
        })
    
    return tasks


def generate_mock_hypotheses(count=15):
    """Generate mock hypotheses for testing."""
    categories = ["performance", "accuracy", "cost_optimization", "reliability"]
    statuses = ["proposed", "testing", "validated", "rejected"]
    
    hypotheses = []
    for i in range(count):
        created = datetime.now() - timedelta(days=random.randint(1, 30))
        hypotheses.append({
            "id": i + 1,
            "hypothesis": f"Mock hypothesis {i+1}: Improve {random.choice(['latency', 'accuracy', 'cost', 'throughput'])} by {random.randint(10, 50)}%",
            "category": random.choice(categories),
            "status": random.choice(statuses),
            "priority": random.choice(["low", "medium", "high"]),
            "created_at": created.isoformat(),
            "test_results": {"score": random.uniform(0.5, 1.0)} if random.random() > 0.5 else None,
        })
    
    return hypotheses


def generate_mock_benchmarks(count=50):
    """Generate mock benchmark data for testing."""
    models = [
        "gpt-4o-mini", "claude-3-haiku", "gemini-1.5-flash", 
        "deepseek-chat", "llama-3.1-8b", "qwen-2.5-7b"
    ]
    task_types = ["planning", "reasoning", "json_output", "code_generation"]
    
    benchmarks = []
    for i in range(count):
        timestamp = datetime.now() - timedelta(hours=random.randint(1, 168))
        model = random.choice(models)
        task_type = random.choice(task_types)
        
        benchmarks.append({
            "id": i + 1,
            "model_name": model,
            "task_type": task_type,
            "quality_score": round(random.uniform(0.5, 1.0), 3),
            "latency_ms": random.randint(200, 5000),
            "cost_usd": round(random.uniform(0.0001, 0.01), 6),
            "timestamp": timestamp.isoformat(),
            "success": random.random() > 0.1,
        })
    
    return benchmarks


def generate_mock_logs(count=100):
    """Generate mock log entries."""
    levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    sources = [
        "cognitive_planner", "tool_web_search", "cognitive_memory",
        "interface_webui", "core.kernel", "core.event_bus"
    ]
    
    logs = []
    for i in range(count):
        timestamp = datetime.now() - timedelta(minutes=random.randint(1, 120))
        level = random.choice(levels)
        
        messages = {
            "INFO": [
                "Plugin initialized successfully",
                "Task completed",
                "Event processed",
                "API request successful"
            ],
            "WARNING": [
                "Rate limit approaching",
                "Cache miss",
                "Slow query detected"
            ],
            "ERROR": [
                "Plugin execution failed",
                "Database connection error",
                "API timeout"
            ],
            "DEBUG": [
                "Processing event",
                "Cache hit",
                "Plugin discovery complete"
            ]
        }
        
        logs.append({
            "id": i + 1,
            "timestamp": timestamp.isoformat(),
            "level": level,
            "source": random.choice(sources),
            "message": random.choice(messages[level]),
        })
    
    return logs[::-1]  # Reverse for newest first


# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(title="SOPHIA Dashboard (Mock Mode)")

# Generate mock data once at startup
MOCK_TASKS = generate_mock_tasks()
MOCK_HYPOTHESES = generate_mock_hypotheses()
MOCK_BENCHMARKS = generate_mock_benchmarks()
MOCK_LOGS = generate_mock_logs()


@app.get("/")
async def root():
    """Redirect to dashboard."""
    return {"message": "SOPHIA Dashboard Mock Server", "dashboard": "/dashboard"}


@app.get("/dashboard")
async def get_dashboard():
    """Serve dashboard HTML."""
    dashboard_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
    if not dashboard_path.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    return FileResponse(str(dashboard_path))


@app.get("/api/tasks")
async def get_tasks(limit: int = 20, offset: int = 0):
    """Get mock tasks."""
    tasks = MOCK_TASKS[offset:offset + limit]
    return {
        "tasks": tasks,
        "total": len(MOCK_TASKS),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/hypotheses")
async def get_hypotheses(limit: int = 20, offset: int = 0):
    """Get mock hypotheses."""
    hypotheses = MOCK_HYPOTHESES[offset:offset + limit]
    return {
        "hypotheses": hypotheses,
        "total": len(MOCK_HYPOTHESES),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/benchmarks")
async def get_benchmarks(
    limit: int = 100,
    task_type: str = None,
    model_name: str = None,
):
    """Get mock benchmarks."""
    benchmarks = MOCK_BENCHMARKS
    
    # Filter if requested
    if task_type:
        benchmarks = [b for b in benchmarks if b["task_type"] == task_type]
    if model_name:
        benchmarks = [b for b in benchmarks if model_name.lower() in b["model_name"].lower()]
    
    return {
        "benchmarks": benchmarks[:limit],
        "total": len(benchmarks),
        "limit": limit,
    }


@app.get("/api/logs")
async def get_logs(limit: int = 100, level: str = None):
    """Get mock logs."""
    logs = MOCK_LOGS
    
    if level:
        logs = [log for log in logs if log["level"] == level.upper()]
    
    return {
        "logs": logs[:limit],
        "total": len(logs),
        "limit": limit,
    }


@app.get("/api/stats")
async def get_stats():
    """Get mock statistics."""
    return {
        "total_tasks": len(MOCK_TASKS),
        "active_tasks": len([t for t in MOCK_TASKS if t["status"] == "in_progress"]),
        "completed_tasks": len([t for t in MOCK_TASKS if t["status"] == "completed"]),
        "failed_tasks": len([t for t in MOCK_TASKS if t["status"] == "failed"]),
        "total_hypotheses": len(MOCK_HYPOTHESES),
        "validated_hypotheses": len([h for h in MOCK_HYPOTHESES if h["status"] == "validated"]),
        "total_benchmarks": len(MOCK_BENCHMARKS),
        "avg_quality_score": round(sum(b["quality_score"] for b in MOCK_BENCHMARKS) / len(MOCK_BENCHMARKS), 3),
    }


@app.post("/api/tools/{tool_name}")
async def execute_tool(tool_name: str):
    """Mock tool execution."""
    return {
        "success": True,
        "message": f"Mock: Tool {tool_name} executed (no actual execution in mock mode)",
        "output": f"Mock output from {tool_name}",
    }


# ============================================
# SERVER STARTUP
# ============================================

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("dashboard_mock")
    
    logger.info("=" * 60)
    logger.info("🎭 SOPHIA Dashboard Server - MOCK MODE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📊 Dashboard: http://127.0.0.1:8000/dashboard")
    logger.info("📡 API Endpoints:")
    logger.info("   - /api/tasks")
    logger.info("   - /api/hypotheses")
    logger.info("   - /api/benchmarks")
    logger.info("   - /api/logs")
    logger.info("   - /api/stats")
    logger.info("")
    logger.info("⚠️  MOCK MODE: All data is randomly generated")
    logger.info("   - No database required")
    logger.info("   - No Sophia kernel required")
    logger.info("   - No Ollama required")
    logger.info("   - Perfect for E2E frontend testing")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Start server
    config = Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = Server(config)
    
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard server stopped")

