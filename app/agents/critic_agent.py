from crewai import Agent

def create_critic_agent(llm):
    return Agent(
        role="Output Validator",
        goal="Ensure correctness, completeness, and consistency of structured outputs",
        backstory=(
            "You are a strict reviewer who ensures all outputs meet schema requirements and contain no inconsistencies."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "Review the structured output.\n"
            "Fix the following issues:\n"
            "- Missing fields\n"
            "- Duplicate tasks\n"
            "- Inconsistent data\n"
            "- Ambiguous descriptions\n\n"
            "Return ONLY corrected JSON.\n"
            "Ensure it strictly matches the schema."
        )
    )