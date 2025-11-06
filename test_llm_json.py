#!/usr/bin/env python3
"""
Phase 1 - LLM JSON Extraction Test

Focuses on testing the critical LLM extraction with JSON mode.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugins.cognitive_notes_reader import CognitiveNotesReader
from plugins.tool_local_llm import LocalLLMTool
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

async def test_llm_json_extraction():
    """Test LLM extraction with JSON mode enabled."""
    
    logger.info("=" * 80)
    logger.info("🧪 Phase 1 - LLM JSON Extraction Test")
    logger.info("=" * 80)
    
    # Initialize plugins
    llm_plugin = LocalLLMTool()
    llm_plugin.setup({"local_llm": {"model": "llama3.1:8b"}})
    
    notes_reader = CognitiveNotesReader()
    notes_reader.setup({
        "all_plugins_map": {"tool_local_llm": llm_plugin},
        "offline_mode": True
    })
    
    # Read notes file
    notes_path = Path("roberts-notes.txt")
    if not notes_path.exists():
        logger.error("❌ roberts-notes.txt not found!")
        return False
    
    notes_content = notes_path.read_text(encoding="utf-8")
    logger.info(f"📄 Reading {len(notes_content)} bytes from roberts-notes.txt")
    
    # Test extraction
    logger.info("\n🔍 Calling LLM extraction (with JSON mode)...")
    tasks = await notes_reader._extract_tasks_from_notes(notes_content)
    
    if not tasks:
        logger.error("❌ FAILED: No tasks extracted!")
        logger.error("   LLM may not be returning valid JSON")
        return False
    
    logger.info(f"\n✅ SUCCESS: Extracted {len(tasks)} tasks")
    logger.info("=" * 80)
    
    for i, task in enumerate(tasks, 1):
        priority = task.get('priority', '?')
        instruction = task.get('instruction', 'N/A')
        category = task.get('category', 'unknown')
        
        logger.info(f"\n📌 Task {i}:")
        logger.info(f"   Priority:    {priority}")
        logger.info(f"   Category:    {category}")
        logger.info(f"   Instruction: {instruction[:100]}...")
    
    logger.info("\n" + "=" * 80)
    logger.info("🎉 TEST PASSED - LLM JSON extraction working!")
    logger.info("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_llm_json_extraction())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
