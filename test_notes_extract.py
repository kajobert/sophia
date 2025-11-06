#!/usr/bin/env python3
"""Direct test of cognitive_notes_reader LLM extraction."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugins.cognitive_notes_reader import CognitiveNotesReaderPlugin
from plugins.tool_local_llm import LocalLLMTool
from core.context import SharedContext
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_extraction():
    """Test LLM extraction from notes."""
    
    # Initialize plugins
    llm_plugin = LocalLLMTool({"offline_mode": True})
    
    notes_reader = CognitiveNotesReaderPlugin({
        "all_plugins_map": {"tool_local_llm": llm_plugin},
        "offline_mode": True
    })
    
    # Read notes file
    with open("roberts-notes.txt", "r", encoding="utf-8") as f:
        notes_content = f.read()
    
    logger.info(f"Read {len(notes_content)} bytes from roberts-notes.txt")
    
    # Call extraction
    tasks = await notes_reader._extract_tasks_from_notes(notes_content)
    
    logger.info(f"Extracted {len(tasks)} tasks")
    for i, task in enumerate(tasks, 1):
        logger.info(f"  Task {i}: priority={task.get('priority')}, category={task.get('category')}")
        logger.info(f"         instruction={task.get('instruction')[:80]}...")
    
    return tasks

if __name__ == "__main__":
    results = asyncio.run(test_extraction())
    print(f"\n✅ Test complete. Extracted {len(results)} tasks.")
