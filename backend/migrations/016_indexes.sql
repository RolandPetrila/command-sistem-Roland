-- Migration 016: Additional indexes for frequently queried tables
-- Tables that had FK columns or ORDER BY columns without indexes

-- chat_messages: queried by session_id (FK, no existing index)
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

-- chat_sessions: queried with ORDER BY updated_at DESC
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated ON chat_sessions(updated_at DESC);

-- task_runs: queried by task_id (FK, used in LEFT JOIN)
CREATE INDEX IF NOT EXISTS idx_task_runs_task ON task_runs(task_id);

-- uptime_history: queried by monitor_id (FK)
CREATE INDEX IF NOT EXISTS idx_uptime_history_monitor ON uptime_history(monitor_id);

-- journal_entries: queried with ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_journal_created ON journal_entries(created_at DESC);

-- bookmarks: queried with ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON bookmarks(created_at DESC);

-- glossary_terms: queried by client_id (FK added in migration 015)
CREATE INDEX IF NOT EXISTS idx_glossary_client ON glossary_terms(client_id);

-- scheduled_tasks: queried by enabled + next_run for scheduler
CREATE INDEX IF NOT EXISTS idx_tasks_enabled_next ON scheduled_tasks(enabled, next_run);

INSERT INTO schema_version (version, name) VALUES (16, '016_indexes');
