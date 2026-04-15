import requests
import json
import logging
from app.schemas.output_schema import OutputSchema

logger = logging.getLogger(__name__)


class SlackTool:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_message(self, text: str):
        payload = {"text": text}

        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise Exception(f"Slack error: {response.text}")

        return {"status": "sent"}


def format_for_slack(output: OutputSchema) -> str:
    lines = []

    lines.append("*📌 Tasks:*")
    for t in output.tasks:
        lines.append(f"- {t.title} (Owner: {t.owner}, Deadline: {t.deadline})")

    lines.append("\n*🧠 Decisions:*")
    for d in output.decisions:
        lines.append(f"- {d.decision} (By: {d.made_by})")

    lines.append("\n*⚠️ Risks:*")
    for r in output.risks:
        lines.append(f"- {r.risk} [Severity: {r.severity}]")

    lines.append("\n*📝 Summary:*")
    lines.append(output.summary)

    return "\n".join(lines)


def format_for_slack_compact(output: OutputSchema) -> str:
    lines = []
    lines.append(f"*🤖 AI Chief of Staff:* {len(output.tasks)} tasks, {len(output.decisions)} decisions, {len(output.risks)} risks")
    if output.tasks:
        lines.append("\n*Top Tasks:*")
        for t in output.tasks[:3]:
            lines.append(f"• {t.title}")
    return "\n".join(lines)
