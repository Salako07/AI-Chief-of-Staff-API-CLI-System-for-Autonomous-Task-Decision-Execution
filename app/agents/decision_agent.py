from crewai import Agent

def create_decision_agent(llm):
    return Agent(
        role="Decision Analyst",
        goal="Extract decisions from business input",
        backstory=(
            "You identify decisions that have been made or implied in conversations."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "Extract all decisions.\n"
            "Each decision must include:\n"
            "- decision\n"
            "- made_by (if available)\n\n"
            "Return ONLY JSON matching the Decision schema."
        )
    )