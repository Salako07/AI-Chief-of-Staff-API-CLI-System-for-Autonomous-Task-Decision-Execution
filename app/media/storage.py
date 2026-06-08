"""Persistent storage helpers for media uploads and transcription jobs."""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)


class MediaStorage:
    """Wrapper around PostgreSQL for media + transcription persistence."""

    def __init__(self, database_url: Optional[str] = None, minconn: int = 1, maxconn: int = 10):
        self.database_url = database_url or os.getenv("DATABASE_URL") or self._build_url_from_parts()
        if not self.database_url:
            self.database_url = "postgresql://ai_chief_user:change_me_in_production@localhost:5432/ai_chief_of_staff"
        self._minconn = minconn
        self._maxconn = maxconn
        self.pool: Optional[SimpleConnectionPool] = None
        self._connect()

    def _connect(self) -> None:
        try:
            self.pool = SimpleConnectionPool(self._minconn, self._maxconn, dsn=self.database_url)
            logger.info("[MEDIA_STORAGE] Connection pool initialized")
            self._ensure_tables()
        except Exception as exc:
            logger.error(f"[MEDIA_STORAGE] DB not available at startup (will retry on first request): {exc}")
            self.pool = None

    def _ensure_connected(self) -> None:
        if self.pool is None:
            self._connect()
        if self.pool is None:
            raise RuntimeError("Database unavailable. Check DATABASE_URL and ensure the database is running.")

    @staticmethod
    def _build_url_from_parts() -> Optional[str]:
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB")
        if user and password and db:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return None

    @contextmanager
    def _get_cursor(self):
        self._ensure_connected()
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def _ensure_tables(self) -> None:
        """Create tables if they do not exist (safety net for local dev)."""
        create_media_files = """
            CREATE TABLE IF NOT EXISTS media_files (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                filename VARCHAR(255) NOT NULL,
                original_path VARCHAR(500) NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                size_bytes BIGINT NOT NULL,
                duration_seconds INTEGER,
                status VARCHAR(50) NOT NULL CHECK(status IN ('uploaded', 'processing', 'completed', 'failed')),
                spaces_key VARCHAR(500),
                spaces_url TEXT,
                storage_type VARCHAR(20) DEFAULT 'local' CHECK(storage_type IN ('local', 'spaces')),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """

        create_jobs = """
            CREATE TABLE IF NOT EXISTS transcription_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                media_id UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
                run_id UUID,
                status VARCHAR(50) NOT NULL CHECK(status IN ('queued', 'processing', 'completed', 'failed')),
                progress INTEGER DEFAULT 0,
                transcription TEXT,
                tasks JSONB,
                decisions JSONB,
                risks JSONB,
                summary TEXT,
                error_message TEXT,
                processing_time_ms INTEGER,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """

        with self._get_cursor() as cursor:
            try:
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
            except Exception as ext_err:
                logger.warning(
                    "[MEDIA_STORAGE] Could not ensure pgcrypto extension (might already exist or insufficient privileges): %s",
                    ext_err
                )
            cursor.execute(create_media_files)
            cursor.execute(create_jobs)
            logger.info("[MEDIA_STORAGE] Tables verified")

    # ------------------------------------------------------------------
    # Media file helpers
    # ------------------------------------------------------------------
    def create_media_file(
        self,
        media_id: str,
        filename: str,
        file_path: str,
        mime_type: str,
        size_bytes: int,
        duration_seconds: Optional[int] = None,
        status: str = "uploaded",
        spaces_key: Optional[str] = None,
        spaces_url: Optional[str] = None,
        storage_type: str = "local"
    ) -> Dict[str, Any]:
        query = """
            INSERT INTO media_files (
                id, filename, original_path, mime_type, size_bytes, duration_seconds,
                status, spaces_key, spaces_url, storage_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """

        params = (
            media_id,
            filename,
            file_path,
            mime_type,
            size_bytes,
            duration_seconds,
            status,
            spaces_key,
            spaces_url,
            storage_type
        )

        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_media_file(self, media_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM media_files WHERE id = %s;"
        with self._get_cursor() as cursor:
            cursor.execute(query, (media_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_media_file(self, media_id: str, **fields) -> Optional[Dict[str, Any]]:
        if not fields:
            return self.get_media_file(media_id)

        assignments: List[str] = []
        values: List[Any] = []
        for key, value in fields.items():
            assignments.append(f"{key} = %s")
            values.append(value)
        assignments.append("updated_at = NOW()")
        values.append(media_id)

        query = f"UPDATE media_files SET {', '.join(assignments)} WHERE id = %s RETURNING *;"

        with self._get_cursor() as cursor:
            cursor.execute(query, tuple(values))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_media_file(self, media_id: str) -> None:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM media_files WHERE id = %s;", (media_id,))

    def delete_old_media_files(self, days_old: int) -> List[Dict[str, Any]]:
        query = """
            DELETE FROM media_files
            WHERE created_at < NOW() - INTERVAL %s
            RETURNING id, original_path;
        """
        interval = f"{days_old} days"
        with self._get_cursor() as cursor:
            cursor.execute(query, (interval,))
            rows = cursor.fetchall() or []
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Transcription job helpers
    # ------------------------------------------------------------------
    def create_transcription_job(self, job_id: str, media_id: str, status: str = "queued") -> Dict[str, Any]:
        query = """
            INSERT INTO transcription_jobs (id, media_id, status, progress)
            VALUES (%s, %s, %s, %s)
            RETURNING *;
        """
        params = (job_id, media_id, status, 0)
        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_transcription_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM transcription_jobs WHERE id = %s;"
        with self._get_cursor() as cursor:
            cursor.execute(query, (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_transcription_job(self, job_id: str, **fields) -> Optional[Dict[str, Any]]:
        if not fields:
            return self.get_transcription_job(job_id)

        assignments: List[str] = []
        values: List[Any] = []
        json_fields = {"tasks", "decisions", "risks"}

        for key, value in fields.items():
            if key in json_fields and value is not None:
                assignments.append(f"{key} = %s")
                values.append(Json(value))
            else:
                assignments.append(f"{key} = %s")
                values.append(value)

        assignments.append("updated_at = NOW()")
        values.append(job_id)

        query = f"UPDATE transcription_jobs SET {', '.join(assignments)} WHERE id = %s RETURNING *;"

        with self._get_cursor() as cursor:
            cursor.execute(query, tuple(values))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_transcription_job(self, job_id: str) -> None:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM transcription_jobs WHERE id = %s;", (job_id,))

    def delete_old_transcription_jobs(self, days_old: int) -> List[str]:
        query = """
            DELETE FROM transcription_jobs
            WHERE created_at < NOW() - INTERVAL %s
            RETURNING id;
        """
        interval = f"{days_old} days"
        with self._get_cursor() as cursor:
            cursor.execute(query, (interval,))
            rows = cursor.fetchall() or []
            return [row["id"] for row in rows]

    def count_active_jobs(self) -> int:
        query = """
            SELECT COUNT(*) AS total
            FROM transcription_jobs
            WHERE status IN ('queued', 'processing');
        """
        with self._get_cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone() or {"total": 0}
            return int(row["total"])


_storage_instance: Optional[MediaStorage] = None


def get_media_storage() -> MediaStorage:
    """Return singleton MediaStorage instance (per process)."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MediaStorage()
    return _storage_instance
