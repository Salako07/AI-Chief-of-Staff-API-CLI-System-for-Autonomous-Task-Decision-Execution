from crewai import Agent

def create_summary_agent(llm):
    return Agent(
        role="Summary Generator",
        goal="Generate a clear human-readable summary",
        backstory=(
            "You summarize structured outputs into concise and readable insights."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "Generate a concise summary of:\n"
            "- Tasks\n"
            "- Decisions\n"
            "- Risks\n\n"
            "Keep it short and clear."
        )
    )