import pytest

from core.neocortex import Neocortex
from core.context import SharedContext
from core.memory_systems import ShortTermMemory


class SucceedTool:
    def execute(self, **kwargs):
        return "ok"


class FailingTool:
    def execute(self, **kwargs):
        raise RuntimeError("tool failed")


class DummyPlanner:
    def __init__(self, plan_to_return=None):
        self._plan = plan_to_return

    def run_task(self, context):
        # mimic PlannerAgent: attach plan to context.payload
        context.payload.setdefault("plan", self._plan)
        return context


@pytest.mark.asyncio
async def test_neocortex_repairs_and_continues(monkeypatch):
    # Prepare Neocortex with one successful tool and one failing tool
    async def _run():
        nc = Neocortex(llm=None, short_term_memory=ShortTermMemory())

        # patch tools: step1 uses SucceedTool, step2 uses FailingTool
        nc.tools = {"SucceedTool": SucceedTool(), "FailingTool": FailingTool()}

        # planner will return a replacement step for the failing step
        replacement = [
            {
                "step_id": 2,
                "description": "replacement",
                "tool_name": "SucceedTool",
                "parameters": {},
            }
        ]
        nc.planner = DummyPlanner(plan_to_return=replacement)

        ctx = SharedContext(session_id="s-repair", original_prompt="run")
        ctx.current_plan = [
            {
                "step_id": 1,
                "description": "ok",
                "tool_name": "SucceedTool",
                "parameters": {},
            },
            {
                "step_id": 2,
                "description": "will fail",
                "tool_name": "FailingTool",
                "parameters": {},
            },
            {
                "step_id": 3,
                "description": "final",
                "tool_name": "SucceedTool",
                "parameters": {},
            },
        ]

        result = await nc.execute_plan(ctx)
        assert result.feedback == "Plan executed successfully."
        # ensure replacement step was executed (there should be 3 successes)
        successes = [
            s
            for s in result.step_history
            if s.get("output", {}).get("status") == "success"
        ]
        assert len(successes) >= 3

    await _run()


@pytest.mark.asyncio
async def test_neocortex_aborts_when_planner_fails(monkeypatch):
    async def _run():
        nc = Neocortex(llm=None, short_term_memory=ShortTermMemory())
        nc.tools = {"SucceedTool": SucceedTool(), "FailingTool": FailingTool()}

        # planner returns no plan (failure)
        nc.planner = DummyPlanner(plan_to_return=None)

        ctx = SharedContext(session_id="s-repair-2", original_prompt="run")
        ctx.current_plan = [
            {
                "step_id": 1,
                "description": "ok",
                "tool_name": "SucceedTool",
                "parameters": {},
            },
            {
                "step_id": 2,
                "description": "will fail",
                "tool_name": "FailingTool",
                "parameters": {},
            },
        ]

        result = await nc.execute_plan(ctx)
        assert result.feedback is not None
        assert (
            "aborted" in result.feedback.lower() or "failed" in result.feedback.lower()
        )

    await _run()
