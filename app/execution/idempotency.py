"""
Idempotency Layer: Prevents duplicate action execution.

THIS IS THE MOST CRITICAL COMPONENT.

Without proper idempotency:
- Slack gets spammed with duplicate messages
- Tasks get created multiple times
- Automation loops break
- System becomes unusable in production

RULES:
1. Check action_id before execution
2. Check action_hash for content changes
3. Store execution log immediately after success
4. NEVER execute the same action twice
"""
import sqlite3
import hashlib
import json
import logging
from typing import Optional, List
from datetime import datetime, timezone
from pathlib import Path
from app.schemas.action_schema import Action, ExecutionLog

logger = logging.getLogger(__name__)


class ExecutionStore:
    """
    SQLite-based execution log store with idempotency checks.

    Database schema:
        executed_actions (
            id TEXT PRIMARY KEY,
            action_id TEXT UNIQUE NOT NULL,
            action_hash TEXT NOT NULL,
            action_type TEXT NOT NULL,
            status TEXT NOT NULL,
            executed_at TIMESTAMP NOT NULL,
            error_message TEXT,
            run_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )

    Indexes:
        - action_id (primary key for dedup)
        - action_hash (detect payload changes)
        - run_id (query by processing run)
    """

    def __init__(self, db_path: str = "execution_log.db"):
        """
        Initialize execution store with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create database and tables if they don't exist."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create executed_actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executed_actions (
                id TEXT PRIMARY KEY,
                action_id TEXT UNIQUE NOT NULL,
                action_hash TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('executed', 'failed', 'skipped')),
                executed_at TIMESTAMP NOT NULL,
                error_message TEXT,
                run_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_hash
            ON executed_actions(action_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_run_id
            ON executed_actions(run_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_executed_at
            ON executed_actions(executed_at DESC)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Execution store initialized at {self.db_path}")

    def is_duplicate(self, action_id: str) -> bool:
        """
        Check if action has already been executed.

        Args:
            action_id: Deterministic action ID

        Returns:
            bool: True if action already exists in log
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM executed_actions
            WHERE action_id = ?
            LIMIT 1
        """, (action_id,))

        result = cursor.fetchone()
        conn.close()

        is_dup = result is not None

        if is_dup:
            logger.info(f"[IDEMPOTENCY] Action {action_id[:20]}... already executed - SKIPPING")

        return is_dup

    def has_payload_changed(self, action_id: str, action_hash: str) -> bool:
        """
        Check if action payload has changed since last execution.

        This detects when the same action ID has different content.

        Args:
            action_id: Deterministic action ID
            action_hash: SHA-256 hash of current payload

        Returns:
            bool: True if payload differs from stored hash
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT action_hash FROM executed_actions
            WHERE action_id = ?
            LIMIT 1
        """, (action_id,))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            # Action never executed
            return False

        stored_hash = result[0]
        has_changed = stored_hash != action_hash

        if has_changed:
            logger.warning(
                f"[IDEMPOTENCY] Action {action_id[:20]}... payload changed "
                f"(old: {stored_hash[:8]}... new: {action_hash[:8]}...)"
            )

        return has_changed

    def save_execution(self, log: ExecutionLog):
        """
        Save execution log entry.

        Args:
            log: ExecutionLog object

        Raises:
            sqlite3.IntegrityError: If action_id already exists (duplicate)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO executed_actions (
                    id, action_id, action_hash, action_type,
                    status, executed_at, error_message, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.id,
                log.action_id,
                log.action_hash,
                log.action_type,
                log.status,
                log.executed_at.isoformat(),
                log.error_message,
                log.run_id
            ))

            conn.commit()
            logger.debug(f"[IDEMPOTENCY] Saved execution log for {log.action_id[:20]}...")

        except sqlite3.IntegrityError as e:
            logger.error(f"[IDEMPOTENCY] Failed to save log (duplicate?): {e}")
            raise

        finally:
            conn.close()

    def get_executions_by_run(self, run_id: str) -> List[ExecutionLog]:
        """
        Get all executions for a specific processing run.

        Args:
            run_id: Processing run ID

        Returns:
            List[ExecutionLog]: List of execution logs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, action_id, action_hash, action_type, status,
                   executed_at, error_message, run_id
            FROM executed_actions
            WHERE run_id = ?
            ORDER BY executed_at ASC
        """, (run_id,))

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append(ExecutionLog(
                id=row[0],
                action_id=row[1],
                action_hash=row[2],
                action_type=row[3],
                status=row[4],
                executed_at=datetime.fromisoformat(row[5]),
                error_message=row[6],
                run_id=row[7]
            ))

        return logs

    def get_recent_executions(self, limit: int = 100) -> List[ExecutionLog]:
        """
        Get most recent executions across all runs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List[ExecutionLog]: Recent execution logs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, action_id, action_hash, action_type, status,
                   executed_at, error_message, run_id
            FROM executed_actions
            ORDER BY executed_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append(ExecutionLog(
                id=row[0],
                action_id=row[1],
                action_hash=row[2],
                action_type=row[3],
                status=row[4],
                executed_at=datetime.fromisoformat(row[5]),
                error_message=row[6],
                run_id=row[7]
            ))

        return logs

    def clear_all(self):
        """
        Delete all execution logs (use with caution).

        This should ONLY be used in testing/development.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM executed_actions")

        conn.commit()
        conn.close()

        logger.warning("[IDEMPOTENCY] All execution logs cleared")

    def get_stats(self) -> dict:
        """
        Get execution statistics.

        Returns:
            dict: Stats including total, executed, failed, skipped counts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'executed' THEN 1 ELSE 0 END) as executed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
            FROM executed_actions
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            "total": row[0] or 0,
            "executed": row[1] or 0,
            "failed": row[2] or 0,
            "skipped": row[3] or 0
        }


def compute_action_hash(action: Action) -> str:
    """
    Compute SHA-256 hash of action payload.

    Args:
        action: Action object

    Returns:
        str: SHA-256 hash (hex digest)
    """
    # Serialize payload to JSON (sorted keys for consistency)
    payload_json = json.dumps(action.payload, sort_keys=True)

    # Hash it
    return hashlib.sha256(payload_json.encode()).hexdigest()
