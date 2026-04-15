from crewai import Agent

def create_critic_agent(llm):
    return Agent(
        role="Output Validator",
        goal="Validate and refine structured JSON outputs for correctness and consistency",
        backstory=(
            "You are a meticulous JSON validator who ensures all outputs meet schema requirements, "
            "removes duplicates, and fixes inconsistencies. You always return valid JSON."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
        instructions=(
            "You will receive JSON input with tasks, decisions, and risks.\n\n"
            "YOUR JOB:\n"
            "1. Validate all fields are present and correctly typed\n"
            "2. Remove duplicate entries (same title/decision/risk)\n"
            "3. Fix any inconsistencies or formatting issues\n"
            "4. Ensure schema compliance\n\n"
            "REQUIRED OUTPUT FORMAT:\n"
            '{\n'
            '  "tasks": [{...}],\n'
            '  "decisions": [{...}],\n'
            '  "risks": [{...}]\n'
            '}\n\n'
            "CRITICAL RULES:\n"
            "- Output ONLY valid JSON - no explanations, no markdown, no code blocks\n"
            "- If input is already valid, return it unchanged\n"
            "- Your output must be directly parseable by json.loads()\n"
            "- Use double quotes for all strings"
        )
    )