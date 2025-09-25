from crewai import Agent, Task, Crew
from core.context import SharedContext


class ArchitectAgent:
    """
    A wrapper class for the Architect agent.
    """

    def __init__(self, llm):
        self.agent = Agent(
            role="Software Architect",
            goal="Design a detailed, robust, and scalable software architecture based on the provided system description.",
            backstory="You are a seasoned Software Architect with years of experience in designing complex, scalable, and maintainable systems. You think in terms of components, modules, data flows, and technology stacks.",
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )
        self.task_description_template = (
            "Based on the following system description, design a comprehensive software architecture. "
            "System Description: {system_description}"
        )
        self.expected_output_template = (
            "A detailed architecture document outlining the main components, their responsibilities, "
            "the data flow between them, and the recommended technology stack."
        )

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Takes a SharedContext object and runs the architect task.
        """
        system_description = context.payload.get("system_description")
        if not system_description:
            raise ValueError(
                "The 'system_description' is missing from the context payload."
            )

        task_description = self.task_description_template.format(
            system_description=system_description
        )

        architect_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=self.expected_output_template,
        )

        crew = Crew(agents=[self.agent], tasks=[architect_task], verbose=False)

        result = crew.kickoff()

        if hasattr(result, "raw"):
            architecture = result.raw
        else:
            architecture = str(result)

        context.payload["architecture"] = architecture
        return context

    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
