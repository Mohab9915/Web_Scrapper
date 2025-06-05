-- Project URLs table (updated with user_id)
CREATE TABLE IF NOT EXISTS project_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    conditions TEXT NOT NULL,
    display_format TEXT NOT NULL DEFAULT 'table' CHECK (display_format IN ('table', 'paragraph', 'raw')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, url)
);

-- Add indexes for faster lookups
CREATE INDEX IF NOT EXISTS project_urls_project_id_idx ON project_urls(project_id);
CREATE INDEX IF NOT EXISTS project_urls_url_idx ON project_urls(url);

-- Add RLS policies
ALTER TABLE project_urls ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users
CREATE POLICY project_urls_policy ON project_urls
    USING (true)
    WITH CHECK (true);
