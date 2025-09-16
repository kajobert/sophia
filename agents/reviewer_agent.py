from crewai import Agent, Task
from crewai_tools import tool
import core.llm_config


class ReviewerAgent:
    """
    This class contains the logic and tools for the Reviewer Agent.
    """
    @tool("Code Diff Review Tool")
    def review_diff(self, diff: str) -> str:
        """
        Analyzes a git diff to ensure documentation is updated alongside code.
        The tool checks if changes to .py files are accompanied by changes to WORKLOG.md.
        """
        # A simple string search is sufficient for this basic implementation.
        # We check for file paths in the diff command to be more specific.
        has_py_changes = ".py" in diff and "diff --git" in diff
        has_worklog_changes = "WORKLOG.md" in diff and "diff --git" in diff

        if has_py_changes and not has_worklog_changes:
            return "FAIL: The WORKLOG.md was not updated alongside code changes."
        else:
            return "PASS"


class ReviewerAgentWrapper:
    """
    A wrapper for the Reviewer Agent that handles its creation and task definition.
    """

    def __init__(self):
        agent_logic = ReviewerAgent()

        self.agent = Agent(
            role='Documentation Reviewer',
            goal='Verify that code changes are accompanied by corresponding documentation updates in WORKLOG.md.',
            backstory='An meticulous agent dedicated to maintaining the integrity and clarity of the project\'s documentation. It ensures that every technical step is chronicled, preventing knowledge loss and ensuring project traceability.',
            verbose=True,
            llm=core.llm_config.llm,
            tools=[agent_logic.review_diff]
        )

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent

    def get_review_task(self, diff_content: str) -> Task:
        """
        Creates a task for the Reviewer Agent to review a diff.
        """
        return Task(
            description=(
                "Agent dostane na vstup textový `diff` změn z Pull Requestu. "
                "Jeho úkolem je analyzovat tento diff. The diff is:\n\n"
                f"{diff_content}"
            ),
            expected_output=(
                'A simple "PASS" or "FAIL" string. "FAIL" must be '
                'followed by a brief, one-sentence reason.'
            ),
            agent=self.agent
        )
