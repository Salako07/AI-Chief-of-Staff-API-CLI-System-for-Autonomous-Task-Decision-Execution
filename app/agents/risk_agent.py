from crewai import Agent

from app.schemas.output_schema import RiskList

def create_risk_agent(llm):
    return Agent(
        role="Risk Detection Specialist",
        goal="Identify risks, blockers, and uncertainties, - Must be a JSON array []",
        backstory=(
            "You analyze business communication to detect potential risks, missing information, and blockers.- Must be a JSON array []"
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
        #output_pydantic=RiskList,
        instructions=(
            "Identify RISKS, BLOCKERS, and UNCERTAINTIES from the input.\n\n"

            "REQUIRED OUTPUT FORMAT:\n"
            "Return ONLY a valid JSON object:\n"
            '{"risks": [\n'
            '  {\n'
            '    "risk": "Clear and specific risk description",\n'
            '    "severity": "low|medium|high",\n'
            '    "mitigation": "Concrete mitigation action or \"none\""\n'
            '  }\n'
            ']}\n\n'

            "CRITICAL RULES:\n"
            "- Use ONLY these fields: risk, severity, mitigation\n"
            "- Use double quotes for all strings\n"
            "- Output ONLY JSON (no markdown, no explanations)\n"
            "- NEVER include id, timestamp, or extra fields\n"

            "\nSEVERITY RULES:\n"
            "- high: will block execution or cause failure\n"
            "- medium: may cause delay or reduced quality\n"
            "- low: minor issue or informational concern\n"

            "\nMITIGATION RULES:\n"
            "- Must be a concrete action\n"
            "- If no mitigation exists, use \"none\"\n"
            "- NEVER use null\n"

            "\nQUALITY RULES:\n"
            "- Only include risks that are explicitly implied or strongly suggested\n"
            "- Avoid generic statements like 'lack of communication'\n"
            "- Every risk must affect execution outcome\n"

            "\nEMPTY CASE:\n"
            "- If no risks found, return: {\"risks\": []}"
           " Only infer when explicitly supported by input context."
            "If not explicitly stated or strongly implied, return 'unknown' or omit."
            "Do NOT add new actions or suggestions."
        )
    )