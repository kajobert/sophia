#!/usr/bin/env python3
"""
Test improved prompts and JSON parsing.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.kernel import SophiaKernel
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_prompts():
    """Test improved prompts with various queries."""
    
    test_cases = [
        "Ahoj, kdo jsi?",
        "Jaké jsou tvé schopnosti?",
        "Kolik je hodin?",
        "Co je v souboru config/settings.yaml?",
    ]
    
    # Temporarily use v2 prompts
    os.rename("config/prompts/planner_offline_prompt.txt", "config/prompts/planner_offline_prompt_old.txt")
    os.rename("config/prompts/sophia_dna_offline.txt", "config/prompts/sophia_dna_offline_old.txt")
    os.rename("config/prompts/planner_offline_prompt_v2.txt", "config/prompts/planner_offline_prompt.txt")
    os.rename("config/prompts/sophia_dna_offline_v2.txt", "config/prompts/sophia_dna_offline.txt")
    
    try:
        kernel = SophiaKernel(mode="single_run", offline_mode=True)
        
        for i, query in enumerate(test_cases, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"TEST {i}: {query}")
            logger.info(f"{'='*60}")
            
            result = await kernel.run_single_query(query)
            
            logger.info(f"\n✅ Result: {result}")
            logger.info(f"{'='*60}\n")
            
            # Small delay between tests
            await asyncio.sleep(2)
    
    finally:
        # Restore original prompts
        os.rename("config/prompts/planner_offline_prompt.txt", "config/prompts/planner_offline_prompt_v2.txt")
        os.rename("config/prompts/sophia_dna_offline.txt", "config/prompts/sophia_dna_offline_v2.txt")
        os.rename("config/prompts/planner_offline_prompt_old.txt", "config/prompts/planner_offline_prompt.txt")
        os.rename("config/prompts/sophia_dna_offline_old.txt", "config/prompts/sophia_dna_offline.txt")

if __name__ == "__main__":
    asyncio.run(test_prompts())
