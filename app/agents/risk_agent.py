from crewai import Agent

def create_risk_agent(llm):
    return Agent(
        role="Risk Detection Specialist",
        goal="Identify risks, blockers, and uncertainties",
        backstory=(
            "You analyze business communication to detect potential risks, missing information, and blockers."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "Identify risks or blockers.\n"
            "Each risk must include:\n"
            "- risk\n"
            "- severity (low, medium, high)\n"
            "- mitigation (if possible)\n\n"
            "Return ONLY JSON matching the Risk schema."
        )
    )