from crewai import Agent

def create_task_agent(llm):
    return Agent(
        role="Task Extraction Specialist",
        goal="Extract structured actionable tasks from input text",
        backstory=(
            "You identify all actionable items from business communication and convert them into structured tasks."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "Extract all actionable tasks.\n"
            "Each task MUST include:\n"
            "- title\n"
            "- owner (if available, else null)\n"
            "- deadline (if available, else null)\n"
            "- priority (default: medium)\n"
            "- status (default: pending)\n\n"
            "Return ONLY valid JSON matching the Task schema.\n"
            "Do NOT include explanations."
        )
    )