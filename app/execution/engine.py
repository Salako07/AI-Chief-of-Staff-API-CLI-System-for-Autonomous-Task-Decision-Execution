"""
Execution Engine: Orchestrates action routing with idempotency control.

EXECUTION FLOW:
1. Receive actions from planner
2. Check idempotency (skip if duplicate)
3. Route to appropriate executor (Slack, Email, Webhook)
4. Log execution result
5. Return summary

CRITICAL: This layer must NEVER modify actions or make decisions.
It only executes deterministic actions from the planner.
"""
import logging
import time
from typing import List, Optional
from app.schemas.action_schema import Action, ExecutionResult, ExecutionLog, ExecutionSummary
from app.execution.idempotency import ExecutionStore, compute_action_hash
from app.tools.slack_tool import SlackTool
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Routes actions to appropriate executors (Slack, Email, Webhook).
    """

    def __init__(self, slack_webhook_url: Optional[str] = None):
        """
        Initialize executor with integration credentials.

        Args:
            slack_webhook_url: Slack webhook URL (optional)
        """
        self.slack_webhook_url = slack_webhook_url
        self.slack_tool = SlackTool(slack_webhook_url) if slack_webhook_url else None

    def execute_slack(self, action: Action) -> ExecutionResult:
        """
        Execute Slack notification action.

        Args:
            action: Action with type="slack"

        Returns:
            ExecutionResult: Execution outcome
        """
        start_time = time.time()

        if not self.slack_tool:
            error_msg = "Slack webhook not configured"
            logger.error(f"[EXECUTOR] {error_msg}")
            return ExecutionResult(
                action_id=action.id,
                action_type="slack",
                success=False,
                status="failed",
                error_message=error_msg,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        try:
            # Skip individual Slack notifications - summary is sent by processor
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(f"[EXECUTOR] Slack action skipped (summary notification only): {action.id[:20]}... (target: {action.target}, {duration_ms}ms)")

            return ExecutionResult(
                action_id=action.id,
                action_type="slack",
                success=True,
                status="skipped",
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            logger.error(f"[EXECUTOR] Slack action failed: {action.id[:20]}... - {error_msg}")

            return ExecutionResult(
                action_id=action.id,
                action_type="slack",
                success=False,
                status="failed",
                error_message=error_msg,
                duration_ms=duration_ms
            )

    def _format_slack_message(self, action: Action) -> str:
        """
        Format action into Slack message.

        Args:
            action: Action object

        Returns:
            str: Formatted Slack message
        """
        lines = []

        # Title
        lines.append(f"*{action.title}*")

        # Payload details
        payload = action.payload

        if "title" in payload:
            lines.append(f"Task: {payload['title']}")

        if "owner" in payload:
            owner = payload['owner'] if payload['owner'] else "_unassigned_"
            lines.append(f"Owner: {owner}")

        if "deadline" in payload:
            deadline = payload['deadline'] if payload['deadline'] else "_no deadline_"
            lines.append(f"Deadline: {deadline}")

        if "priority" in payload:
            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(payload.get("priority"), "⚪")
            lines.append(f"Priority: {priority_emoji} {payload['priority']}")

        if "decision" in payload:
            lines.append(f"Decision: {payload['decision']}")

        if "made_by" in payload:
            lines.append(f"Made by: {payload['made_by']}")

        if "risk" in payload:
            lines.append(f"Risk: {payload['risk']}")

        if "severity" in payload:
            lines.append(f"Severity: {payload['severity']}")

        if "mitigation" in payload:
            if payload['mitigation']:
                lines.append(f"Mitigation: {payload['mitigation']}")

        return "\n".join(lines)

    def execute_email(self, action: Action) -> ExecutionResult:
        """
        Execute email notification action.

        Args:
            action: Action with type="email"

        Returns:
            ExecutionResult: Execution outcome
        """
        # Placeholder for email integration
        logger.warning(f"[EXECUTOR] Email execution not yet implemented: {action.id[:20]}...")

        return ExecutionResult(
            action_id=action.id,
            action_type="email",
            success=False,
            status="failed",
            error_message="Email executor not implemented",
            duration_ms=0
        )

    def execute_webhook(self, action: Action) -> ExecutionResult:
        """
        Execute webhook/API call action.

        Args:
            action: Action with type="webhook"

        Returns:
            ExecutionResult: Execution outcome
        """
        # Placeholder for webhook integration
        logger.warning(f"[EXECUTOR] Webhook execution not yet implemented: {action.id[:20]}...")

        return ExecutionResult(
            action_id=action.id,
            action_type="webhook",
            success=False,
            status="failed",
            error_message="Webhook executor not implemented",
            duration_ms=0
        )


class ExecutionEngine:
    """
    Main execution orchestrator with idempotency control.

    CRITICAL DESIGN RULES:
    1. ALWAYS check idempotency before execution
    2. ALWAYS log execution results
    3. NEVER execute the same action twice
    4. Execution must be deterministic
    """

    def __init__(self, store: ExecutionStore, executor: ActionExecutor):
        """
        Initialize execution engine.

        Args:
            store: Execution log store for idempotency
            executor: Action executor (Slack, Email, Webhook router)
        """
        self.store = store
        self.executor = executor

    def execute_actions(
        self,
        actions: List[Action],
        run_id: str,
        force: bool = False
    ) -> ExecutionSummary:
        """
        Execute actions with idempotency control.

        Args:
            actions: List of actions to execute
            run_id: Processing run ID
            force: If True, skip idempotency check (DANGEROUS - use only for testing)

        Returns:
            ExecutionSummary: Summary of all executions
        """
        start_time = time.time()

        logger.info(f"[ENGINE] Starting execution for run {run_id}: {len(actions)} actions")

        results = []
        executed_count = 0
        skipped_count = 0
        failed_count = 0

        for action in actions:
            # STEP 1: Idempotency check
            if not force and self.store.is_duplicate(action.id):
                # Action already executed - SKIP
                result = ExecutionResult(
                    action_id=action.id,
                    action_type=action.type,
                    success=False,
                    status="skipped",
                    error_message="Already executed (idempotency check)"
                )

                # DON'T save log entry - it already exists in DB (that's why we're skipping!)
                # The action_id has UNIQUE constraint, so saving would cause SQL error

                results.append(result)
                skipped_count += 1
                continue

            # STEP 2: Execute action
            if action.type == "slack":
                result = self.executor.execute_slack(action)
            elif action.type == "email":
                result = self.executor.execute_email(action)
            elif action.type == "webhook":
                result = self.executor.execute_webhook(action)
            else:
                result = ExecutionResult(
                    action_id=action.id,
                    action_type=action.type,
                    success=False,
                    status="failed",
                    error_message=f"Unknown action type: {action.type}"
                )

            # STEP 3: Log execution
            self.store.save_execution(ExecutionLog(
                action_id=action.id,
                action_hash=compute_action_hash(action),
                action_type=action.type,
                status=result.status,
                error_message=result.error_message,
                run_id=run_id
            ))

            # Track stats
            if result.success:
                executed_count += 1
            else:
                if result.status == "skipped":
                    skipped_count += 1
                else:
                    failed_count += 1

            results.append(result)

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"[ENGINE] Execution complete for run {run_id}: "
            f"{executed_count} executed, {skipped_count} skipped, {failed_count} failed "
            f"({duration_ms}ms total)"
        )

        return ExecutionSummary(
            run_id=run_id,
            total_actions=len(actions),
            executed=executed_count,
            skipped=skipped_count,
            failed=failed_count,
            duration_ms=duration_ms,
            results=results
        )
