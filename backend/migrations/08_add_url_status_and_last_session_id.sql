-- Add status and last_scraped_session_id columns to project_urls table
ALTER TABLE project_urls
ADD COLUMN status TEXT DEFAULT 'pending',
ADD COLUMN last_scraped_session_id UUID REFERENCES scrape_sessions(id) ON DELETE SET NULL;

-- Add an index for the new status column
CREATE INDEX IF NOT EXISTS project_urls_status_idx ON project_urls(status);

-- Update existing rows to have a default status if they don't have one
-- For existing URLs, we can't be sure of their true status,
-- so 'pending' is a safe default. If they have associated scrape_sessions,
-- they might be 'completed', but this requires more complex logic to backfill.
-- For simplicity, we'll set to 'pending'.
UPDATE project_urls SET status = 'pending' WHERE status IS NULL;
