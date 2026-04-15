from app.agents.decision_agent import create_decision_agent
from app.agents.execution_agent import create_execution_agent
from app.agents.intake_agent import create_intake_agent
from app.agents.task_agent import create_task_agent
from app.agents.summary_agent import create_summary_agent
from app.agents.risk_agent import create_risk_agent
from app.agents.critic_agent import create_critic_agent
from app.schemas.output_schema import TaskList, DecisionList, RiskList, OutputSchema, AgentMetadata, Task, Decision, Risk
import json
import uuid
import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from typing import List

logger = logging.getLogger(__name__)

# Quality control constants
MIN_QUALITY_SCORE = 5


# ============================================================================
# ENHANCED DEDUPLICATION FUNCTIONS
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for deduplication comparison.
    Removes extra whitespace, converts to lowercase, strips punctuation.
    """
    import re
    # Convert to lowercase and strip
    normalized = text.lower().strip()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    # Remove common punctuation at the end
    normalized = normalized.rstrip('.!?')
    return normalized


def deduplicate_tasks(tasks: List[Task]) -> List[Task]:
    """
    Deduplicate tasks based on normalized title.
    Keeps the first occurrence of each unique task.
    """
    seen = set()
    unique = []
    duplicates_removed = 0

    for task in tasks:
        key = normalize_text(task.title)
        if key not in seen:
            seen.add(key)
            unique.append(task)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        logger.info(f"Enhanced deduplication: Removed {duplicates_removed} duplicate tasks")

    return unique


def deduplicate_decisions(decisions: List[Decision]) -> List[Decision]:
    """
    Deduplicate decisions based on normalized decision text.
    Keeps the first occurrence of each unique decision.
    """
    seen = set()
    unique = []
    duplicates_removed = 0

    for decision in decisions:
        key = normalize_text(decision.decision)
        if key not in seen:
            seen.add(key)
            unique.append(decision)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        logger.info(f"Enhanced deduplication: Removed {duplicates_removed} duplicate decisions")

    return unique


def deduplicate_risks(risks: List[Risk]) -> List[Risk]:
    """
    Deduplicate risks based on normalized risk text.
    Keeps the first occurrence of each unique risk.
    """
    seen = set()
    unique = []
    duplicates_removed = 0

    for risk in risks:
        key = normalize_text(risk.risk)
        if key not in seen:
            seen.add(key)
            unique.append(risk)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        logger.info(f"Enhanced deduplication: Removed {duplicates_removed} duplicate risks")

    return unique


# ============================================================================
# QUALITY SCORING SYSTEM
# ============================================================================

def compute_quality_score(tasks: List[Task], decisions: List[Decision], risks: List[Risk]) -> int:
    """
    Compute a quality score for the extracted data.

    Scoring rules:
    - Each task: +2 points
    - Each decision: +1 point
    - Each risk: +1 point

    Penalties:
    - Task missing owner: -1 point
    - Task missing deadline: -1 point
    - Risk missing mitigation: -0.5 points

    Returns:
        int: Quality score (can be negative in worst cases)
    """
    score = 0

    # Base points
    score += len(tasks) * 2
    score += len(decisions)
    score += len(risks)

    # Penalties for incomplete tasks
    for task in tasks:
        if not task.owner or task.owner in ["unknown", "unassigned", None]:
            score -= 1
        if not task.deadline or task.deadline in ["unknown", None, ""]:
            score -= 1

    # Penalties for incomplete risks
    for risk in risks:
        if not risk.mitigation or risk.mitigation in ["unknown", None, ""]:
            score -= 0.5

    return int(score)


class AIChiefOfStaffProcessor:
    def __init__(self, llm, tools, db, slack_webhook_url: str = None):
        self.llm = llm
        self.tools = tools
        self.db = db
        self.slack_webhook_url = slack_webhook_url
        self.intake_agent = create_intake_agent(llm)
        self.task_agent = create_task_agent(llm)
        self.decision_agent = create_decision_agent(llm)
        self.risk_agent = create_risk_agent(llm)
        self.execution_agent = create_execution_agent(llm, tools)
        self.summary_agent = create_summary_agent(llm)
        self.critic_agent = create_critic_agent(llm)


    def process_input(self, text: str, max_retries: int = 2) -> OutputSchema:
        """
        Process input with quality-based retry loop.

        Args:
            text: Input text to process
            max_retries: Maximum number of retry attempts (default: 2)

        Returns:
            OutputSchema: Validated and quality-checked output
        """
        run_id = str(uuid.uuid4())
        logger.info(f"[{run_id}] Starting processing with quality control (max_retries={max_retries})")

        for attempt in range(max_retries + 1):
            logger.info(f"[{run_id}] Attempt {attempt + 1}/{max_retries + 1}")

            # Run the pipeline
            result = self._run_pipeline(text, run_id)

            # Compute quality score
            quality_score = compute_quality_score(result.tasks, result.decisions, result.risks)
            logger.info(f"[{run_id}] Quality score: {quality_score} (threshold: {MIN_QUALITY_SCORE})")

            # Check if quality is acceptable
            if quality_score >= MIN_QUALITY_SCORE:
                logger.info(f"[{run_id}] Quality threshold met! Returning result.")

                # Send Slack notification if configured
                self._send_slack_notification(result, run_id)

                return result

            # Log quality issues
            if attempt < max_retries:
                logger.warning(
                    f"[{run_id}] Low quality output (score: {quality_score}). "
                    f"Retrying with stricter prompt (attempt {attempt + 2}/{max_retries + 1})"
                )
                # Enhance prompt for next iteration
                text = f"Be more precise and structured. Provide complete information:\n{text}"
            else:
                logger.warning(
                    f"[{run_id}] Quality score {quality_score} below threshold {MIN_QUALITY_SCORE}, "
                    f"but max retries reached. Returning best-effort result."
                )

        # Send Slack notification for final result (even if low quality)
        self._send_slack_notification(result, run_id)

        return result

    def _run_pipeline(self, text: str, run_id: str) -> OutputSchema:
        """
        Core processing pipeline (formerly process_input).

        Args:
            text: Input text to process
            run_id: Unique identifier for this processing run

        Returns:
            OutputSchema: Validated output
        """
        logger.info(f"[{run_id}] Starting processing pipeline")

        # Step 1: Intake and preprocess input
        logger.info(f"[{run_id}] Running intake agent")
        preprocessed_input = self.intake_agent.kickoff(text)
        logger.debug(f"[{run_id}] Preprocessed input: {preprocessed_input}")

        # Step 2: Extract tasks, decisions, and risks
        logger.info(f"[{run_id}] Running extraction agents")
        tasks_raw = self.task_agent.kickoff(json.dumps(preprocessed_input, default=str), response_format=TaskList)
        decisions_raw = self.decision_agent.kickoff(json.dumps(preprocessed_input, default=str), response_format=DecisionList)
        risks_raw = self.risk_agent.kickoff(json.dumps(preprocessed_input, default=str), response_format=RiskList)

        # Parse raw JSON outputs into structured data
        tasks_json = normalize_output(tasks_raw.raw)
        decisions_json = normalize_output(decisions_raw.raw)
        risks_json = normalize_output(risks_raw.raw)

        # Schema validation: ensure required keys exist
        if "tasks" not in tasks_json:
            logger.error(f"[{run_id}] Missing 'tasks' key in agent output. Got: {tasks_json}")
            tasks_json["tasks"] = []

        if "decisions" not in decisions_json:
            logger.error(f"[{run_id}] Missing 'decisions' key in agent output. Got: {decisions_json}")
            decisions_json["decisions"] = []

        if "risks" not in risks_json:
            logger.error(f"[{run_id}] Missing 'risks' key in agent output. Got: {risks_json}")
            risks_json["risks"] = []

        tasks = tasks_json.get("tasks", [])
        decisions = decisions_json.get("decisions", [])
        risks = risks_json.get("risks", [])

        state = {
            "tasks": tasks,
            "decisions": decisions,
            "risks": risks
        }

        # Step 3: Critic refinement loop (smart loop with improvement detection)
        logger.info(f"[{run_id}] Running critic agent (max 2 iterations)")
        for iteration in range(2):
            logger.debug(f"[{run_id}] Critic iteration {iteration + 1}/2")
            try:
                reviewed = self.critic_agent.kickoff(json.dumps(state, default=str))
                new_state = safe_critic_update(state, reviewed.raw)

                # Check if critic made any improvements
                if new_state == state:
                    logger.info(f"[{run_id}] Critic made no changes, stopping early")
                    break

                state = new_state
            except Exception as e:
                logger.warning(f"[{run_id}] Critic iteration {iteration + 1} failed: {e}")
                break

        # Step 3.5: Deduplication (prevent "Schedule meeting" vs "Plan meeting")
        logger.info(f"[{run_id}] Deduplicating outputs")
        state = deduplicate_state(state, run_id)

        # Step 4: Validate with Pydantic (re-enabled with error handling)
        logger.info(f"[{run_id}] Validating outputs with Pydantic")
        validated_tasks = []
        validated_decisions = []
        validated_risks = []

        # Track failures for visibility
        failed_tasks = []
        failed_decisions = []
        failed_risks = []

        for task in state.get("tasks", []):
            try:
                # Remove LLM-generated id/timestamp fields - these are auto-generated by Pydantic
                task_data = {k: v for k, v in task.items() if k not in ['id', 'timestamp']}

                # Normalize priority: null/None → "medium"
                if not task_data.get("priority") or task_data.get("priority") in [None, "null", "None"]:
                    task_data["priority"] = "medium"

                # Normalize owner: "null" string → None
                if task_data.get("owner") in ["null", "None", ""]:
                    task_data["owner"] = None

                validated_tasks.append(Task(**task_data))
            except ValidationError as e:
                logger.error(f"[{run_id}] Task validation failed: {e}. Skipping task: {task}")
                failed_tasks.append(task)

        for decision in state.get("decisions", []):
            try:
                # Remove LLM-generated id/timestamp fields - these are auto-generated by Pydantic
                decision_data = {k: v for k, v in decision.items() if k not in ['id', 'timestamp']}

                # Normalize made_by: "null" string → "unknown"
                if decision_data.get("made_by") in [None, "null", "None", ""]:
                    decision_data["made_by"] = "unknown"

                validated_decisions.append(Decision(**decision_data))
            except ValidationError as e:
                logger.error(f"[{run_id}] Decision validation failed: {e}. Skipping decision: {decision}")
                failed_decisions.append(decision)

        for risk in state.get("risks", []):
            try:
                # Remove LLM-generated id field - this is auto-generated by Pydantic
                risk_data = {k: v for k, v in risk.items() if k not in ['id', 'timestamp']}

                # Normalize severity: null/None → "medium"
                if not risk_data.get("severity") or risk_data.get("severity") in [None, "null", "None"]:
                    risk_data["severity"] = "medium"

                # Normalize mitigation: "null" string → None
                if risk_data.get("mitigation") in ["null", "None", ""]:
                    risk_data["mitigation"] = None

                validated_risks.append(Risk(**risk_data))
            except ValidationError as e:
                logger.error(f"[{run_id}] Risk validation failed: {e}. Skipping risk: {risk}")
                failed_risks.append(risk)

        # Log dropped items for visibility
        if failed_tasks:
            logger.warning(f"[{run_id}]   Dropped {len(failed_tasks)} invalid tasks")
        if failed_decisions:
            logger.warning(f"[{run_id}]   Dropped {len(failed_decisions)} invalid decisions")
        if failed_risks:
            logger.warning(f"[{run_id}]   Dropped {len(failed_risks)} invalid risks")

        logger.info(f"[{run_id}] Validated: {len(validated_tasks)} tasks, {len(validated_decisions)} decisions, {len(validated_risks)} risks")

        # Step 4.5: Enhanced deduplication (after validation, before quality check)
        logger.info(f"[{run_id}] Running enhanced deduplication")
        validated_tasks = deduplicate_tasks(validated_tasks)
        validated_decisions = deduplicate_decisions(validated_decisions)
        validated_risks = deduplicate_risks(validated_risks)

        logger.info(f"[{run_id}] After deduplication: {len(validated_tasks)} tasks, {len(validated_decisions)} decisions, {len(validated_risks)} risks")

        # Quality threshold: ensure we got meaningful output
        if not validated_tasks and not validated_decisions and not validated_risks:
            logger.error(f"[{run_id}]  No valid outputs extracted from any agent!")
            raise ValueError(
                f"Processing failed: No valid tasks, decisions, or risks extracted. "
                f"System output unreliable. Failed items: {len(failed_tasks)} tasks, "
                f"{len(failed_decisions)} decisions, {len(failed_risks)} risks"
            )

        # Step 5: Generate summary
        logger.info(f"[{run_id}] Generating summary")
        summary_raw = self.summary_agent.kickoff(json.dumps(state, default=str))

        # Extract summary string from agent output
        if hasattr(summary_raw, 'raw'):
            summary = str(summary_raw.raw).strip()
        else:
            summary = str(summary_raw).strip()

        # Validate summary length (should be concise)
        word_count = len(summary.split())
        if word_count > 100:
            logger.warning(f"[{run_id}] Summary is too long ({word_count} words). Truncating to 80 words.")
            # Truncate to 80 words
            summary = ' '.join(summary.split()[:80]) + "..."

        logger.debug(f"[{run_id}] Summary ({word_count} words): {summary[:100]}...")

        final_output = OutputSchema(
            tasks=validated_tasks,
            decisions=validated_decisions,
            risks=validated_risks,
            summary=summary,
            metadata=AgentMetadata(
                source="cli",
                processed_at=datetime.now(timezone.utc),
                run_id=run_id
            )
        )

        logger.info(f"[{run_id}] Processing complete")
        return final_output

    def _send_slack_notification(self, result: OutputSchema, run_id: str):
        """
        Send formatted notification to Slack if webhook is configured.

        Args:
            result: OutputSchema to format and send
            run_id: Current run ID for logging
        """
        if not self.slack_webhook_url:
            logger.debug(f"[{run_id}] Slack webhook not configured, skipping notification")
            return

        try:
            from app.tools.slack_tool import SlackTool, format_for_slack

            logger.info(f"[{run_id}] Sending Slack notification...")

            slack = SlackTool(webhook_url=self.slack_webhook_url)
            message = format_for_slack(result)
            slack.send_message(message)

            logger.info(f"[{run_id}] Slack notification sent successfully")

        except Exception as e:
            # Don't fail the entire process if Slack notification fails
            logger.error(f"[{run_id}] Failed to send Slack notification: {e}")


def normalize_output(output):
    """
    Ensures output is always a dictionary.
    Handles both string and dict responses.
    """
    if isinstance(output, dict):
        return output

    if isinstance(output, str):
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}. Output was: {output[:200]}")
            return {}

    logger.warning(f"Unexpected output type: {type(output)}")
    return {}

def safe_critic_update(current_state, critic_output):
    reviewed_json = normalize_output(critic_output)

    # If critic failed, keep previous state
    if not reviewed_json:
        logger.warning("Critic returned invalid output, keeping previous state")
        return current_state

    return {
        "tasks": reviewed_json.get("tasks", current_state["tasks"]),
        "decisions": reviewed_json.get("decisions", current_state["decisions"]),
        "risks": reviewed_json.get("risks", current_state["risks"]),
    }


def deduplicate_state(state, run_id):
    """
    Deduplicate tasks, decisions, and risks based on semantic similarity.
    Simple approach: case-insensitive title/decision/risk comparison.
    """
    def deduplicate_list(items, key_field):
        """Deduplicate a list of dicts based on a key field."""
        seen = set()
        unique_items = []
        duplicates_removed = 0

        for item in items:
            # Normalize the key for comparison
            key_value = str(item.get(key_field, "")).lower().strip()

            if key_value and key_value not in seen:
                seen.add(key_value)
                unique_items.append(item)
            elif key_value:
                duplicates_removed += 1

        return unique_items, duplicates_removed

    # Deduplicate each category
    tasks, task_dups = deduplicate_list(state.get("tasks", []), "title")
    decisions, decision_dups = deduplicate_list(state.get("decisions", []), "decision")
    risks, risk_dups = deduplicate_list(state.get("risks", []), "risk")

    # Log deduplication results
    if task_dups > 0:
        logger.info(f"[{run_id}] Removed {task_dups} duplicate tasks")
    if decision_dups > 0:
        logger.info(f"[{run_id}] Removed {decision_dups} duplicate decisions")
    if risk_dups > 0:
        logger.info(f"[{run_id}] Removed {risk_dups} duplicate risks")

    return {
        "tasks": tasks,
        "decisions": decisions,
        "risks": risks
    }