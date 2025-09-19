import pytest

from crewai.tools import BaseTool
from crewai import Agent


# DummyLLM pro izolované testování bez síťových volání
class DummyLLM:
    def __call__(self, *args, **kwargs):
        return "dummy-response"


class DummyTool(BaseTool):
    name: str = "DummyTool"
    description: str = "Testovací tool pro CrewAI validaci."

    def _run(self, *args, **kwargs):
        return "ok"


@pytest.mark.skip(
    reason="CrewAI agent test nelze robustně izolovat bez hlubšího mockování všech závislostí."
)
def test_philosopher_agent_attrs():
    agent = Agent(
        role="Test",
        goal="Test",
        backstory="Test",
        llm=DummyLLM(),
        tools=[DummyTool()],
        verbose=False,
        allow_delegation=False,
        memory=False,
    )
    assert hasattr(agent, "role")
    assert hasattr(agent, "goal")
    assert hasattr(agent, "llm")
    assert hasattr(agent, "tools")
