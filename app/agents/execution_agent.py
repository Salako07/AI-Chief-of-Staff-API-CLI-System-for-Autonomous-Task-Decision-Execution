from crewai import Agent

def create_execution_agent(llm, tools):
    return Agent(
        role="Operations Executor",
        goal="Execute actions based on structured output",
        backstory=(
            "You take structured data and perform real operations such as storing tasks or triggering actions."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools,
        instructions=(
            "Execute the following:\n"
            "- Store tasks in database\n"
            "- Log all operations\n"
            "- Trigger any necessary actions\n\n"
            "Return execution status."
        )
    )