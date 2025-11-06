import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class CoreSelfDiagnostic(BasePlugin):
    """Lightweight startup self-diagnostic plugin.

    Runs a non-blocking set of smoke checks shortly after setup and records
    the result in `self.last_result`. Designed to be low-risk and fast so it
    can safely run during Kernel initialization in Phase 1.
    """

    @property
    def name(self) -> str:
        return "core_self_diagnostic"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.CORE

    @property
    def version(self) -> str:
        return "0.1.0"

    def __init__(self):
        self.plugin_manager = None
        self.all_plugins = {}
        self.logger = logging.getLogger("plugins.core_self_diagnostic")
        self.offline_mode = False
        self.last_result: Dict[str, Any] | None = None

    def setup(self, config: dict) -> None:
        # Accept injected objects from Kernel
        self.plugin_manager = config.get("plugin_manager")
        self.all_plugins = config.get("all_plugins") or {}
        self.logger = config.get("logger") or self.logger
        self.offline_mode = config.get("offline_mode", False)

        # Schedule background checks (Kernel.initialize is async so this is safe)
        try:
            asyncio.create_task(self._run_checks())
        except RuntimeError:
            # If there's no running loop, run in a new one in background
            loop = asyncio.new_event_loop()
            asyncio.get_event_loop().run_in_executor(None, loop.run_until_complete, self._run_checks())

    async def execute(self, context: SharedContext) -> SharedContext:
        # No-op for now; diagnostics are run on setup in background
        return context

    async def _run_checks(self) -> None:
        """Perform quick, best-effort health checks and record results."""
        # Small delay to allow other plugins to finish setup
        await asyncio.sleep(0.05)

        result: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "plugin_count": 0,
            "memory_plugins": 0,
            "planner_present": False,
            "llm_tool_present": False,
            "offline_mode": bool(self.offline_mode),
            "llm_ping_ok": False,
            "notes": [],
        }

        try:
            if self.plugin_manager and hasattr(self.plugin_manager, "_plugins"):
                # Count all registered plugins
                total = sum(len(v) for v in self.plugin_manager._plugins.values())
                result["plugin_count"] = total
                # Memory plugin count
                mem_count = len(self.plugin_manager.get_plugins_by_type(PluginType.MEMORY))
                result["memory_plugins"] = mem_count
            else:
                result["notes"].append("plugin_manager not provided or missing _plugins")

            # Check for planner
            planner = self.all_plugins.get("cognitive_planner")
            result["planner_present"] = planner is not None

            # Check for an LLM tool (local preferred when offline)
            if self.offline_mode:
                llm = self.all_plugins.get("tool_local_llm")
            else:
                llm = self.all_plugins.get("tool_llm") or self.all_plugins.get("tool_local_llm")

            result["llm_tool_present"] = llm is not None

            # If an LLM tool exists, do a tiny ping
            if llm and hasattr(llm, "execute"):
                try:
                    ctx = SharedContext(
                        session_id="selfdiag",
                        current_state="DIAGNOSTIC",
                        logger=self.logger,
                        user_input="(diagnostic) ping",
                        history=[],
                        use_event_driven=False,
                        offline_mode=self.offline_mode,
                    )
                    # Give the LLM a short timeout
                    resp = await asyncio.wait_for(llm.execute(context=ctx), timeout=8.0)
                    # Record any textual response
                    llm_resp = resp.payload.get("llm_response") if hasattr(resp, "payload") else None
                    result["llm_ping_ok"] = True if llm_resp is not None else True
                    result["notes"].append(f"LLM response sample: {str(llm_resp)[:200]}")
                except asyncio.TimeoutError:
                    result["llm_ping_ok"] = False
                    result["notes"].append("LLM ping timed out")
                except Exception as e:
                    result["llm_ping_ok"] = False
                    result["notes"].append(f"LLM ping error: {e}")

        except Exception as e:
            result["notes"].append(f"Exception during diagnostics: {e}")

        # Persist result for introspection/tests
        self.last_result = result

        # Try to write to log file via tool_file_system if present for easy debugging
        try:
            fs = None
            if self.plugin_manager:
                for p in self.plugin_manager.get_plugins_by_type(PluginType.TOOL):
                    if getattr(p, "name", "") == "tool_file_system":
                        fs = p
                        break

            if fs and hasattr(fs, "write_file"):
                # write a JSON summary
                try:
                    await fs.write_file(SharedContext(session_id="selfdiag", current_state="DIAGNOSTIC", logger=self.logger), "self_diagnostic.json", json.dumps(result, indent=2))
                except Exception:
                    # best-effort only
                    pass
            else:
                # Fallback to regular logger
                self.logger.info("Self-diagnostic result: %s", json.dumps(result))
        except Exception:
            pass
