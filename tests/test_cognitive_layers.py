
from core.cognitive_layers import ReptilianBrain, MammalianBrain, Neocortex
from core.memory_systems import LongTermMemory, ShortTermMemory
from core.context import SharedContext


def test_reptilian_rejects_empty_prompt():
    rb = ReptilianBrain()
    ctx = SharedContext(session_id="s1", original_prompt="")
    out = rb.process_input(ctx)
    assert out.payload["reptilian"]["accepted"] is False


def test_reptilian_classification():
    rb = ReptilianBrain()
    prompt = "Short prompt"
    ctx = SharedContext(session_id="s2", original_prompt=prompt)
    out = rb.process_input(ctx)
    assert out.payload["reptilian"]["accepted"] is True
    assert out.payload["preprocessed"]["classification"] == "short"


def test_mammalian_enriches_with_ltm():
    ltm = LongTermMemory()
    ltm.add_record("Previously solved prompt about optimization")
    mb = MammalianBrain(long_term_memory=ltm)
    ctx = SharedContext(session_id="s3", original_prompt="optimization")
    out = mb.process_input(ctx)
    assert "ltm_matches" in out.payload["mammalian"]


def test_neocortex_stores_and_requests_plan(monkeypatch):
    stm = ShortTermMemory()

    class DummyPlanner:
        def run_task(self, context):
            context.payload.setdefault(
                "plan",
                [
                    {
                        "step_id": 1,
                        "description": "noop",
                        "tool_name": "ListDirectoryTool",
                        "parameters": {},
                    }
                ],
            )
            return context

    planner = DummyPlanner()
    nc = Neocortex(short_term_memory=stm, planner=planner)
    ctx = SharedContext(session_id="s4", original_prompt="list files")
    out = nc.process_input(ctx)
    assert out.payload.get("plan") is not None
    stored = stm.get("s4")
    assert "plan" in stored
