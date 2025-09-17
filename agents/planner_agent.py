from crewai import Agent, Task, Crew
from core.context import SharedContext
from tools.ethical_reviewer import EthicalReviewTool
from core.agent_config import load_agent_config

class PlannerAgent:
    """
    A wrapper class for the Planner agent.
    """
    def __init__(self, llm):
        agent_config = load_agent_config("planner")
        self.agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            llm=llm,
            tools=[EthicalReviewTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
        self.task_description_template = agent_config['task_description']
        self.expected_output_template = agent_config['expected_output']

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Runs the planning task using the provided context.

        Args:
            context: The shared context object containing the original prompt.

        Returns:
            The updated shared context with the plan in the payload.
        """
        task_description = self.task_description_template.format(
            original_prompt=context.original_prompt
        )

        planning_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=self.expected_output_template
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[planning_task],
            verbose=True
        )

        result = crew.kickoff()

        output = result.raw if hasattr(result, 'raw') else str(result)

        review_keyword = "Ethical Review Feedback:"
        if review_keyword in output:
            parts = output.split(review_keyword, 1)
            plan = parts[0].strip()
            ethical_review = review_keyword + parts[1].strip()
        else:
            plan = output
            ethical_review = "Ethical review not found in the output."

        context.payload['plan'] = plan
        context.payload['ethical_review'] = ethical_review

        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
