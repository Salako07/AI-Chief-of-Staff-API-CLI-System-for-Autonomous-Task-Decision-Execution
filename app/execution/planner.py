"""
Execution Planner: Converts canonical state into deterministic actions.

CRITICAL RULES:
1. NEVER execute directly from LLM output - always use canonical state
2. NEVER trust LLM-generated action IDs - generate them deterministically
3. Action generation must be deterministic (same state = same actions)
4. No "creative" behavior - strict rule-based mapping
"""
import hashlib
import json
from typing import List, Dict, Any
from app.schemas.action_schema import Action
from app.schemas.output_schema import OutputSchema
import logging

logger = logging.getLogger(__name__)


def generate_action_id(action_type: str, entity_type: str, entity_id: str, target: str) -> str:
    """
    Generate deterministic action ID from action parameters.

    Args:
        action_type: Type of action (slack, email, etc.)
        entity_type: Type of entity (task, decision, risk)
        entity_id: Unique ID of the entity
        target: Target destination

    Returns:
        str: Deterministic action ID

    Example:
        >>> generate_action_id("slack", "task", "abc-123", "#ops")
        'slack-task-abc123-ops-e8f2a9b4'
    """
    # Create deterministic string
    key = f"{action_type}:{entity_type}:{entity_id}:{target}"

    # Hash it for uniqueness
    hash_suffix = hashlib.sha256(key.encode()).hexdigest()[:8]

    # Clean IDs (remove special chars)
    clean_id = entity_id.replace("-", "")[:12]
    clean_target = target.replace("#", "").replace("@", "")[:10]

    return f"{action_type}-{entity_type}-{clean_id}-{clean_target}-{hash_suffix}"


def compute_action_hash(action: Dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of action payload for idempotency checks.

    Args:
        action: Action dictionary

    Returns:
        str: SHA-256 hash
    """
    # Use only payload for hash (excludes status, timestamps, etc.)
    payload_str = json.dumps(action.get("payload", {}), sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()


class ExecutionPlanner:
    """
    Converts canonical state into executable actions.

    Rule set:
    - Tasks → Slack notification to #ops-channel
    - Decisions → Slack notification to #ops-channel
    - High-severity risks → Slack alert to #alerts channel
    - Medium/low risks → Logged but not notified
    """

    def __init__(self, slack_target: str = "#ops-channel", alerts_target: str = "#alerts"):
        """
        Initialize execution planner with target channels.

        Args:
            slack_target: Default Slack channel for tasks/decisions
            alerts_target: Slack channel for high-severity risks
        """
        self.slack_target = slack_target
        self.alerts_target = alerts_target

    def build_actions(self, output: OutputSchema, run_id: str) -> List[Action]:
        """
        Build deterministic actions from canonical state.

        Args:
            output: Validated OutputSchema with tasks, decisions, risks
            run_id: Processing run ID for traceability

        Returns:
            List[Action]: List of actions to execute
        """
        actions = []

        logger.info(f"[{run_id}] Building actions from state: {len(output.tasks)} tasks, {len(output.decisions)} decisions, {len(output.risks)} risks")

        # RULE 1: Tasks → Slack notifications
        for task in output.tasks:
            # Use task TITLE as deterministic key (not auto-generated UUID)
            action_id = generate_action_id("slack", "task", task.title, self.slack_target)

            actions.append(Action(
                id=action_id,
                type="slack",
                title=f"Task Assigned: {task.title}",
                payload={
                    "id": task.id,
                    "title": task.title,
                    "owner": task.owner,
                    "deadline": task.deadline,
                    "priority": task.priority,
                    "status": task.status
                },
                target=self.slack_target
            ))

        # RULE 2: Decisions → Slack notifications
        for decision in output.decisions:
            # Use decision TEXT as deterministic key (not auto-generated UUID)
            action_id = generate_action_id("slack", "decision", decision.decision, self.slack_target)

            actions.append(Action(
                id=action_id,
                type="slack",
                title=f"Decision Made: {decision.decision}",
                payload={
                    "id": decision.id,
                    "decision": decision.decision,
                    "made_by": decision.made_by,
                    "timestamp": str(decision.timestamp)
                },
                target=self.slack_target
            ))

        # RULE 3: High-severity risks → Slack alerts
        for risk in output.risks:
            if risk.severity == "high":
                # Use risk TEXT as deterministic key (not auto-generated UUID)
                action_id = generate_action_id("slack", "risk", risk.risk, self.alerts_target)

                actions.append(Action(
                    id=action_id,
                    type="slack",
                    title=f"🚨 HIGH RISK: {risk.risk}",
                    payload={
                        "id": risk.id,
                        "risk": risk.risk,
                        "severity": risk.severity,
                        "mitigation": risk.mitigation
                    },
                    target=self.alerts_target
                ))

        logger.info(f"[{run_id}] Generated {len(actions)} actions")

        return actions

    def build_actions_with_rules(
        self,
        output: OutputSchema,
        run_id: str,
        rules: Dict[str, Any] = None
    ) -> List[Action]:
        """
        Build actions with custom rule set.

        Args:
            output: Validated OutputSchema
            run_id: Processing run ID
            rules: Custom rules (overrides defaults)

        Returns:
            List[Action]: List of actions

        Example rules:
            {
                "notify_tasks": True,
                "notify_decisions": False,
                "risk_severity_threshold": "medium",
                "slack_target": "#custom-channel"
            }
        """
        if rules is None:
            return self.build_actions(output, run_id)

        actions = []

        # Apply custom rules
        slack_target = rules.get("slack_target", self.slack_target)
        notify_tasks = rules.get("notify_tasks", True)
        notify_decisions = rules.get("notify_decisions", True)
        risk_threshold = rules.get("risk_severity_threshold", "high")

        if notify_tasks:
            for task in output.tasks:
                action_id = generate_action_id("slack", "task", task.id, slack_target)
                actions.append(Action(
                    id=action_id,
                    type="slack",
                    title=f"Task: {task.title}",
                    payload={"title": task.title, "owner": task.owner},
                    target=slack_target
                ))

        if notify_decisions:
            for decision in output.decisions:
                action_id = generate_action_id("slack", "decision", decision.id, slack_target)
                actions.append(Action(
                    id=action_id,
                    type="slack",
                    title=f"Decision: {decision.decision}",
                    payload={"decision": decision.decision},
                    target=slack_target
                ))

        # Filter risks by threshold
        severity_levels = {"low": 0, "medium": 1, "high": 2}
        threshold_level = severity_levels.get(risk_threshold, 2)

        for risk in output.risks:
            risk_level = severity_levels.get(risk.severity, 0)
            if risk_level >= threshold_level:
                action_id = generate_action_id("slack", "risk", risk.id, slack_target)
                actions.append(Action(
                    id=action_id,
                    type="slack",
                    title=f"⚠️ {risk.severity.upper()} RISK: {risk.risk}",
                    payload={"risk": risk.risk, "severity": risk.severity},
                    target=slack_target
                ))

        return actions
