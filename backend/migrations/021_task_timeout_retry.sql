-- Migration 021: Add timeout, retry columns to scheduled_tasks (R4-09)
-- Add scheduler pause/resume support columns

ALTER TABLE scheduled_tasks ADD COLUMN timeout_seconds INTEGER DEFAULT 300;
ALTER TABLE scheduled_tasks ADD COLUMN max_retries INTEGER DEFAULT 1;
ALTER TABLE scheduled_tasks ADD COLUMN retry_count INTEGER DEFAULT 0;

INSERT INTO schema_version (version, name) VALUES (21, '021_task_timeout_retry');
