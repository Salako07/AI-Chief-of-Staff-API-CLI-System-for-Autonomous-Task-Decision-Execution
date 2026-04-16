"""
PostgreSQL-based Execution Store for idempotency and audit logging.

WHY POSTGRESQL:
- Persistent storage (survives restarts)
- ACID transactions (no race conditions)
- Rich querying for analytics
- Production-grade reliability
- Scales to millions of records
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.schemas.action_schema import ExecutionLog

logger = logging.getLogger(__name__)


class PostgreSQLExecutionStore:
    """
    PostgreSQL-based execution log with idempotency checks.

    Features:
    - UNIQUE constraint on action_id prevents duplicates
    - Connection pooling for performance
    - Automatic retries on connection failures
    - Rich analytics queries
    """

    def __init__(self, database_url: str = None):
        """
        Initialize PostgreSQL connection pool.

        Args:
            database_url: PostgreSQL connection string
                         Format: postgresql://user:password@host:port/database
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://ai_chief_user:change_me_in_production@localhost:5432/ai_chief_of_staff"
        )

        # Create connection pool (5-20 connections)
        try:
            self.pool = SimpleConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=self.database_url
            )
            logger.info("[POSTGRES] Connection pool initialized")
            self._init_tables()
        except Exception as e:
            logger.error(f"[POSTGRES] Failed to initialize connection pool: {e}")
            raise

    def _get_connection(self):
        """Get connection from pool."""
        return self.pool.getconn()

    def _return_connection(self, conn):
        """Return connection to pool."""
        self.pool.putconn(conn)

    def _init_tables(self):
        """
        Ensure tables exist (tables should be created by init_db.sql).
        This is a safety check.
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'executed_actions'
                    );
                """)
                exists = cursor.fetchone()[0]

                if not exists:
                    logger.warning("[POSTGRES] executed_actions table does not exist. Run init_db.sql first!")

            conn.commit()
            logger.info("[POSTGRES] Database tables verified")
        except Exception as e:
            conn.rollback()
            logger.error(f"[POSTGRES] Failed to verify tables: {e}")
        finally:
            self._return_connection(conn)

    def is_duplicate(self, action_id: str) -> bool:
        """
        Check if action has already been executed.

        Args:
            action_id: Deterministic action ID

        Returns:
            bool: True if already executed, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM executed_actions WHERE action_id = %s LIMIT 1",
                    (action_id,)
                )
                result = cursor.fetchone()

                if result is not None:
                    logger.info(f"[IDEMPOTENCY] Action {action_id[:30]}... already executed - SKIPPING")

                return result is not None
        finally:
            self._return_connection(conn)

    def has_payload_changed(self, action_id: str, action_hash: str) -> bool:
        """
        Detect if action payload changed since last execution.

        Args:
            action_id: Action ID
            action_hash: SHA-256 hash of current payload

        Returns:
            bool: True if payload changed, False otherwise
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT action_hash FROM executed_actions WHERE action_id = %s",
                    (action_id,)
                )
                result = cursor.fetchone()

                if result and result[0] != action_hash:
                    logger.warning(f"[IDEMPOTENCY] Payload changed for {action_id[:30]}...")
                    return True

                return False
        finally:
            self._return_connection(conn)

    def save_execution(self, log: ExecutionLog):
        """
        Save execution log to PostgreSQL.

        Args:
            log: ExecutionLog object

        Raises:
            psycopg2.IntegrityError: If action_id already exists (duplicate)
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO executed_actions (
                        id, action_id, action_hash, action_type, status,
                        executed_at, error_message, run_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    log.id,
                    log.action_id,
                    log.action_hash,
                    log.action_type,
                    log.status,
                    log.executed_at,
                    log.error_message,
                    log.run_id
                ))

            conn.commit()
            logger.debug(f"[POSTGRES] Saved execution log for {log.action_id[:30]}...")

        except psycopg2.IntegrityError as e:
            conn.rollback()
            logger.error(f"[IDEMPOTENCY] Failed to save log (duplicate?): {e}")
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"[POSTGRES] Failed to save execution log: {e}")
            raise
        finally:
            self._return_connection(conn)

    def get_executions_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all executions for a specific run.

        Args:
            run_id: Processing run ID

        Returns:
            List[Dict]: List of execution records
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id, action_id, action_type, status,
                        executed_at, error_message
                    FROM executed_actions
                    WHERE run_id = %s
                    ORDER BY executed_at ASC
                """, (run_id,))

                return cursor.fetchall()
        finally:
            self._return_connection(conn)

    def get_recent_executions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent executions across all runs.

        Args:
            limit: Maximum number of records to return

        Returns:
            List[Dict]: List of execution records
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id, action_id, action_type, status,
                        executed_at, error_message, run_id
                    FROM executed_actions
                    ORDER BY executed_at DESC
                    LIMIT %s
                """, (limit,))

                return cursor.fetchall()
        finally:
            self._return_connection(conn)

    def get_stats(self, run_id: Optional[str] = None) -> Dict[str, int]:
        """
        Get execution statistics.

        Args:
            run_id: Optional run_id to filter stats

        Returns:
            Dict: Statistics (total, executed, skipped, failed)
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if run_id:
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total,
                            COUNT(*) FILTER (WHERE status = 'executed') as executed,
                            COUNT(*) FILTER (WHERE status = 'skipped') as skipped,
                            COUNT(*) FILTER (WHERE status = 'failed') as failed
                        FROM executed_actions
                        WHERE run_id = %s
                    """, (run_id,))
                else:
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total,
                            COUNT(*) FILTER (WHERE status = 'executed') as executed,
                            COUNT(*) FILTER (WHERE status = 'skipped') as skipped,
                            COUNT(*) FILTER (WHERE status = 'failed') as failed
                        FROM executed_actions
                    """)

                result = cursor.fetchone()
                return dict(result) if result else {"total": 0, "executed": 0, "skipped": 0, "failed": 0}
        finally:
            self._return_connection(conn)

    def get_failed_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent failed actions for investigation.

        Args:
            limit: Maximum number of records

        Returns:
            List[Dict]: Failed action records
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id, action_id, action_type, error_message,
                        executed_at, run_id
                    FROM executed_actions
                    WHERE status = 'failed'
                    ORDER BY executed_at DESC
                    LIMIT %s
                """, (limit,))

                return cursor.fetchall()
        finally:
            self._return_connection(conn)

    def cleanup_old_logs(self, days: int = 90):
        """
        Delete logs older than specified days (data retention).

        Args:
            days: Number of days to retain

        Returns:
            int: Number of deleted records
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM executed_actions
                    WHERE executed_at < NOW() - INTERVAL '%s days'
                    RETURNING id
                """, (days,))

                deleted_count = cursor.rowcount

            conn.commit()
            logger.info(f"[POSTGRES] Cleaned up {deleted_count} old execution logs (>{days} days)")
            return deleted_count
        except Exception as e:
            conn.rollback()
            logger.error(f"[POSTGRES] Failed to cleanup old logs: {e}")
            return 0
        finally:
            self._return_connection(conn)

    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("[POSTGRES] Connection pool closed")
