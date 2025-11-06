"""Kernel worker that consumes tasks from a persistent queue and executes them via Kernel.process_single_input.

This is a thin adapter for MVP: tasks are expected to have a top-level
`instruction` string which is passed as `user_input` to Kernel.process_single_input.
"""
import asyncio
import logging
from typing import Any

from core.simple_persistent_queue import SimplePersistentQueue
from core.kernel import Kernel
from core.context import SharedContext


class KernelWorker:
    def __init__(self, kernel: Kernel, queue: SimplePersistentQueue, poll_interval: float = 1.0):
        self.kernel = kernel
        self.queue = queue
        self.poll_interval = poll_interval
        self.logger = logging.getLogger("sophia.kernel_worker")
        self._running = False

    async def run(self) -> None:
        self._running = True
        self.logger.info("KernelWorker started")

        # Ensure kernel is initialized
        await self.kernel.initialize()

        while self._running:
            try:
                # Poll queue in thread to avoid blocking
                item = await asyncio.to_thread(self.queue.dequeue_and_lock)
                if not item:
                    await asyncio.sleep(self.poll_interval)
                    continue

                task_id = item.get("id")
                payload = item.get("payload", {})

                instruction = None
                if isinstance(payload, dict):
                    instruction = payload.get("instruction") or payload.get("user_input")
                if not instruction:
                    # fallback to raw payload string
                    instruction = str(payload)

                self.logger.info(f"Processing task {task_id}: {instruction}")

                # Log task start to reflection journal (if plugin available)
                reflection = None
                try:
                    from plugins.base_plugin import PluginType
                    reflection_plugins = self.kernel.plugin_manager.get_plugins_by_type(PluginType.TOOL)
                    reflection = next((p for p in reflection_plugins if p.name == "tool_self_reflection"), None)
                    if reflection:
                        reflection.log_task_start(task_id, instruction)
                except Exception as refl_err:
                    self.logger.debug(f"Reflection logging skipped: {refl_err}")

                # Build a minimal SharedContext and process single input
                context = SharedContext(
                    session_id=f"worker-{task_id}",
                    current_state="WORKER_RUNNING",
                    logger=self.logger,
                    user_input=instruction,
                    history=[],
                )

                try:
                    # run with timeout to prevent blocking forever
                    # Use the full consciousness_loop in single-run mode so plans are
                    # fully executed (process_single_input intentionally doesn't run
                    # multi-step plan execution). The consciousness loop will exit
                    # after processing the single input.
                    await asyncio.wait_for(self.kernel.consciousness_loop(single_run_input=instruction), timeout=300.0)
                    self.logger.info(f"Task {task_id} executed via consciousness_loop")
                    await asyncio.to_thread(self.queue.mark_done, task_id)
                    
                    # Log task completion to reflection journal
                    try:
                        if reflection:
                            reflection.log_task_complete(task_id, f"Task completed successfully: {instruction[:100]}")
                    except Exception as refl_err:
                        self.logger.debug(f"Reflection logging skipped: {refl_err}")
                        
                except Exception as e:
                    self.logger.error(f"Task {task_id} failed during execution: {e}")
                    await asyncio.to_thread(self.queue.mark_failed, task_id, str(e))
                    
                    # Log task failure to reflection journal
                    try:
                        if reflection:
                            reflection.log_task_failed(task_id, str(e))
                    except Exception as refl_err:
                        self.logger.debug(f"Reflection logging skipped: {refl_err}")
                except Exception as e:
                    self.logger.error(f"Task {task_id} failed: {e}")
                    await asyncio.to_thread(self.queue.mark_failed, task_id, str(e))

            except asyncio.CancelledError:
                self._running = False
                break
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
