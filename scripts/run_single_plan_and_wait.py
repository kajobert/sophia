"""Run Kernel in-process for one single input and wait for execution to finish.

This runs the full consciousness loop (single input) so planner and execution phases
are performed in-process and any file writes from tools will occur synchronously.
"""
import os

# Set environment variables BEFORE importing Kernel
os.environ['SOPHIA_DISABLE_INTERACTIVE_PLUGINS'] = '1'
os.environ['SOPHIA_FORCE_LOCAL_ONLY'] = '1'

import asyncio
from core.kernel import Kernel

async def main():
    kernel = Kernel(use_event_driven=False, offline_mode=True)
    await kernel.initialize()

    instruction = (
        'RETURN ONLY a JSON array (no text). Create exactly one step: '
        "[{\"tool_name\":\"tool_file_system\",\"method_name\":\"write_file\",\"arguments\":{\"path\":\"sandbox/headless_test.txt\",\"content\":\"HEADLESS_TEST_OK\"}}]"
    )

    await kernel.consciousness_loop(single_run_input=instruction)
    exit(0)  # Ensure script exits after test


if __name__ == '__main__':
    asyncio.run(main())
