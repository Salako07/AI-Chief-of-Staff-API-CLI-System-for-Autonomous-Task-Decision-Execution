from crewai import Agent
from app.schemas.output_schema import DecisionList
def create_decision_agent(llm):
    return Agent(
        role="Decision Analyst",
        goal="Extract concrete decisions that represent resolved choices or commitments",
        backstory=(
            "You are an expert at identifying decisions - resolved choices, not tasks or actions. "
            "A decision is a choice that has been made, not something that needs to be done."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
        #output_pydantic=DecisionList,
        instructions=(
            "Extract all DECISIONS from the input.\n\n"

            "IMPORTANT:\n"
            "A decision is a RESOLVED and CONFIRMED choice.\n"
            "It is NOT a task, suggestion, or intention.\n\n"

            "GOOD DECISIONS:\n"
            '- "Meeting scheduled for Monday at 2pm"\n'
            '- "Sarah assigned as meeting owner"\n'
            '- "Budget approved at $50k"\n\n'

            "NOT DECISIONS (DO NOT INCLUDE):\n"
            '- "Schedule meeting"\n'
            '- "Prepare agenda"\n'
            '- "We should review budget"\n'
            '- "Finish report"\n\n'

            "REQUIRED OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            '{"decisions": [\n'
            '  {\n'
            '    "decision": "Clear resolved statement",\n'
            '    "made_by": "Person name or unknown"\n'
            '  }\n'
            ']}\n\n'

            "CRITICAL RULES:\n"
            "- Use EXACT field names: decision, made_by\n"
            "- Use double quotes for all JSON\n"
            "- Output ONLY JSON (no markdown, no explanations, no text)\n"
            "- Do NOT include fields like: id, timestamp\n"

            "\nDECISION RULES:\n"
            "- Include ONLY confirmed or strongly implied decisions\n"
            "- If uncertain or speculative, EXCLUDE it\n"
            "- Do NOT restate tasks as decisions\n"
            "- Do NOT include duplicate or overlapping decisions\n"

            "\nMADE_BY RULES:\n"
            "- Assign the person responsible for the decision if clearly stated\n"
            "- If unclear, use 'unknown'\n"
            "- NEVER return null or 'null'\n"

            "\nEMPTY CASE:\n"
            "- If no valid decisions found, return: {\"decisions\": []}"
            "Only infer when explicitly supported by input context."
            "If not explicitly stated or strongly implied, return 'unknown' or omit."
            "Do NOT add new actions or suggestions."
        )
    )