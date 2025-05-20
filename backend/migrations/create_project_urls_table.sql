-- Create project_urls table
CREATE TABLE IF NOT EXISTS project_urls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    conditions TEXT,
    display_format TEXT DEFAULT 'table',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, url)
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS project_urls_project_id_idx ON project_urls(project_id);
CREATE INDEX IF NOT EXISTS project_urls_url_idx ON project_urls(url);
