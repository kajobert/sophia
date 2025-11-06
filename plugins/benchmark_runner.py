"""
BenchmarkRunner Plugin: Autonomous self-debugging/benchmarking loop for Sophia
- Runs benchmark/test scripts (offline/online)
- Analyzes results, detects failures, and triggers self-improvement
- Delegates to Jules for code improvement if needed
- Fully asynchronous, no human intervention required
"""
import asyncio
import logging
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

class BenchmarkRunner(BasePlugin):
    @property
    def name(self):
        return "benchmark_runner"

    @property
    def plugin_type(self):
        return PluginType.COGNITIVE

    @property
    def version(self):
        return "0.1.0"

    def setup(self, config):
        self.logger = config.get("logger", logging.getLogger("benchmark_runner"))
        self.all_plugins = config.get("all_plugins", {})
        self.offline_mode = config.get("offline_mode", False)
        self.jules_plugin = self.all_plugins.get("cognitive_jules_autonomy")
        self.file_system = self.all_plugins.get("tool_file_system")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Main entry: runs the self-benchmarking loop once (can be scheduled repeatedly).
        """
        self.logger.info("[BenchmarkRunner] Starting autonomous benchmark run...")
        # 1. Run benchmark/test script (offline/online)
        result = await self._run_benchmark_script(context)
        # 2. Analyze results
        improvement_needed = self._analyze_benchmark_result(result)
        # 3. If improvement needed, delegate to Jules (online) or trigger self-improvement (offline)
        if improvement_needed:
            self.logger.info("[BenchmarkRunner] Improvement needed, delegating to Jules...")
            await self._delegate_improvement(context, result)
        else:
            self.logger.info("[BenchmarkRunner] No improvement needed. Sophia is stable.")
        return context

    async def _run_benchmark_script(self, context):
        """Run Sophia's main benchmark/test script and return result (simulate subprocess call)."""
        import subprocess
        try:
            script = "test_realworld_workflow.sh" if not self.offline_mode else "prompt_debug_benchmark.py"
            if script.endswith(".sh"):
                proc = await asyncio.create_subprocess_shell(f"bash {script}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            else:
                proc = await asyncio.create_subprocess_exec("python3", script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            output = stdout.decode() + stderr.decode()
            self.logger.info(f"[BenchmarkRunner] Benchmark output:\n{output[:500]}")
            return output
        except Exception as e:
            self.logger.error(f"[BenchmarkRunner] Benchmark script failed: {e}")
            return str(e)

    def _analyze_benchmark_result(self, output):
        """Simple heuristic: look for 'FAIL', 'error', or missing summary report."""
        if "FAIL" in output or "error" in output.lower():
            return True
        if self.file_system:
            try:
                summary = self.file_system.read_file(None, "summary_report.txt")
                if "success" not in summary.lower():
                    return True
            except Exception:
                return True
        return False

    async def _delegate_improvement(self, context, result):
        """Delegate improvement to Jules (if available), regardless of offline_mode."""
        if self.jules_plugin:
            # Compose a task for Jules: e.g., "Fix failing test in ..."
            task = "Analyze and fix Sophia's failing benchmark. See summary_report.txt and logs."
            repo = "ShotyCZ/sophia"
            await self.jules_plugin.delegate_task(context, repo=repo, task=task)
            self.logger.info("[BenchmarkRunner] Delegation to Jules complete.")
        else:
            self.logger.warning("[BenchmarkRunner] No Jules plugin available: cannot delegate. Log for review.")
            if self.file_system:
                self.file_system.append_to_file(None, "benchmark_runner.log", f"Improvement needed: {result}\n")
