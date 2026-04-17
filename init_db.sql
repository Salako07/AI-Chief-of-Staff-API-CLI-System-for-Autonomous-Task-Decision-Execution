-- AI Chief of Staff - PostgreSQL Schema
-- Persistent idempotency and audit logs

-- Ensure UUID generation support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- EXECUTION LOG TABLE (Idempotency + Audit Trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS executed_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_id VARCHAR(255) UNIQUE NOT NULL,
    action_hash VARCHAR(64) NOT NULL,
    action_type VARCHAR(50) NOT NULL CHECK(action_type IN ('slack', 'email', 'webhook', 'notion')),
    status VARCHAR(20) NOT NULL CHECK(status IN ('executed', 'failed', 'skipped')),
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    error_message TEXT,
    run_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT idx_action_id_unique UNIQUE (action_id)
);

-- Index for fast idempotency checks
CREATE INDEX IF NOT EXISTS idx_executed_actions_action_hash ON executed_actions(action_hash);
CREATE INDEX IF NOT EXISTS idx_executed_actions_run_id ON executed_actions(run_id);
CREATE INDEX IF NOT EXISTS idx_executed_actions_executed_at ON executed_actions(executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_executed_actions_status ON executed_actions(status);
CREATE INDEX IF NOT EXISTS idx_executed_actions_action_type ON executed_actions(action_type);

-- ============================================================================
-- PROCESSING RUNS TABLE (Run metadata and statistics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS processing_runs (
    run_id UUID PRIMARY KEY,
    input_text TEXT NOT NULL,
    input_source VARCHAR(50),
    tasks_count INTEGER DEFAULT 0,
    decisions_count INTEGER DEFAULT 0,
    risks_count INTEGER DEFAULT 0,
    quality_score INTEGER,
    processing_duration_ms INTEGER,
    status VARCHAR(20) CHECK(status IN ('processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_processing_runs_created_at ON processing_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_processing_runs_status ON processing_runs(status);

-- ============================================================================
-- TASKS TABLE (Extracted tasks with full history)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES processing_runs(run_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    owner VARCHAR(255),
    deadline VARCHAR(100),
    priority VARCHAR(20) CHECK(priority IN ('low', 'medium', 'high')),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_run_id ON tasks(run_id);
CREATE INDEX IF NOT EXISTS idx_tasks_owner ON tasks(owner);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- ============================================================================
-- DECISIONS TABLE (Extracted decisions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES processing_runs(run_id) ON DELETE CASCADE,
    decision TEXT NOT NULL,
    made_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_run_id ON decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_decisions_made_by ON decisions(made_by);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at DESC);

-- ============================================================================
-- RISKS TABLE (Extracted risks)
-- ============================================================================

CREATE TABLE IF NOT EXISTS risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES processing_runs(run_id) ON DELETE CASCADE,
    risk TEXT NOT NULL,
    severity VARCHAR(20) CHECK(severity IN ('low', 'medium', 'high')),
    mitigation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risks_run_id ON risks(run_id);
CREATE INDEX IF NOT EXISTS idx_risks_severity ON risks(severity);
CREATE INDEX IF NOT EXISTS idx_risks_created_at ON risks(created_at DESC);

-- ============================================================================
-- MEDIA PROCESSING TABLES (Uploads + Transcription Jobs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    duration_seconds INTEGER,
    status VARCHAR(50) NOT NULL CHECK(status IN ('uploaded', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_files_status ON media_files(status);
CREATE INDEX IF NOT EXISTS idx_media_files_created_at ON media_files(created_at DESC);

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcription_jobs_media_id ON transcription_jobs(media_id);
CREATE INDEX IF NOT EXISTS idx_transcription_jobs_status ON transcription_jobs(status);
CREATE INDEX IF NOT EXISTS idx_transcription_jobs_created_at ON transcription_jobs(created_at DESC);

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- Execution statistics by action type
CREATE OR REPLACE VIEW execution_stats_by_type AS
SELECT
    action_type,
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (executed_at - created_at))) as avg_duration_seconds
FROM executed_actions
WHERE executed_at >= NOW() - INTERVAL '30 days'
GROUP BY action_type, status
ORDER BY action_type, status;

-- Daily processing volume
CREATE OR REPLACE VIEW daily_processing_volume AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_runs,
    SUM(tasks_count) as total_tasks,
    SUM(decisions_count) as total_decisions,
    SUM(risks_count) as total_risks,
    AVG(quality_score) as avg_quality_score,
    AVG(processing_duration_ms) as avg_duration_ms
FROM processing_runs
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Failed actions for investigation
CREATE OR REPLACE VIEW failed_actions_log AS
SELECT
    id,
    action_id,
    action_type,
    error_message,
    executed_at,
    run_id
FROM executed_actions
WHERE status = 'failed'
ORDER BY executed_at DESC
LIMIT 100;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to check if action was already executed
CREATE OR REPLACE FUNCTION is_action_executed(p_action_id VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM executed_actions
        WHERE action_id = p_action_id
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get execution statistics
CREATE OR REPLACE FUNCTION get_execution_stats(p_run_id UUID)
RETURNS TABLE(
    total_actions BIGINT,
    executed BIGINT,
    skipped BIGINT,
    failed BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_actions,
        COUNT(*) FILTER (WHERE status = 'executed')::BIGINT as executed,
        COUNT(*) FILTER (WHERE status = 'skipped')::BIGINT as skipped,
        COUNT(*) FILTER (WHERE status = 'failed')::BIGINT as failed
    FROM executed_actions
    WHERE run_id = p_run_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update completed_at timestamp
CREATE OR REPLACE FUNCTION update_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('completed', 'failed') AND OLD.completed_at IS NULL THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_processing_runs_completed
    BEFORE UPDATE ON processing_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_completed_at();

-- ============================================================================
-- INITIAL DATA / GRANTS
-- ============================================================================

-- Grant permissions (if needed for specific roles)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ai_chief_user;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_chief_user;

-- Insert sample data for testing (optional)
-- INSERT INTO processing_runs (run_id, input_text, input_source, status)
-- VALUES (gen_random_uuid(), 'Test input', 'test', 'completed');

COMMENT ON TABLE executed_actions IS 'Idempotency log and audit trail for all executed actions';
COMMENT ON TABLE processing_runs IS 'Metadata and statistics for each processing run';
COMMENT ON TABLE tasks IS 'All extracted tasks with full history';
COMMENT ON TABLE decisions IS 'All extracted decisions';
COMMENT ON TABLE risks IS 'All extracted risks';
