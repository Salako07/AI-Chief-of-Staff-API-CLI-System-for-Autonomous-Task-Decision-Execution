from crewai import Agent

def create_summary_agent(llm):
    return Agent(
        role="Summary Generator",
        goal="Generate a concise, plain-text summary under 80 words",
        backstory=(
            "You are an expert at creating ultra-brief, actionable summaries. "
            "You write in plain text without any markdown formatting."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "Generate a concise summary of the extracted data.\n\n"
            "STRICT REQUIREMENTS:\n"
            "- Maximum 80 words\n"
            "- Plain text only - NO markdown formatting (no **, no #, no bullets)\n"
            "- Focus on: key tasks, critical deadlines, major decisions, high-severity risks\n"
            "- Write in complete sentences, not bullet points\n"
            "- Be specific: mention names, dates, priorities\n\n"
            "GOOD EXAMPLE:\n"
            '"1 task pending: Complete investor report by Friday (owner: John, priority: high). '
            'Decision made: John assigned to financials. 2 high-severity risks identified: '
            'data availability and tight deadline."\n\n'
            "Return ONLY the summary text. No preamble, no explanations, no formatting."
            "Summarize ONLY what exists in the input state."
            "Do NOT add new actions, suggestions, or improvements."
        )
    )