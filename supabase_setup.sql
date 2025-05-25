-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rag_enabled BOOLEAN NOT NULL DEFAULT FALSE
);

-- Scrape sessions table
CREATE TABLE IF NOT EXISTS scrape_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('scraped', 'rag_ingested', 'error')),
    raw_markdown TEXT,
    structured_data_json JSONB,
    structured_data_csv TEXT,
    unique_scrape_identifier TEXT GENERATED ALWAYS AS (project_id::text || '_' || id::text) STORED UNIQUE
);

-- Markdowns table (for RAG)
CREATE TABLE IF NOT EXISTS markdowns (
    id BIGSERIAL PRIMARY KEY,
    unique_name TEXT NOT NULL UNIQUE,
    url TEXT,
    markdown TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Embeddings table (for RAG)
CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    unique_name TEXT NOT NULL,
    chunk_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_chunk_per_doc UNIQUE (unique_name, chunk_id)
);

-- Function for similarity search with filtering
CREATE OR REPLACE FUNCTION match_embeddings_filtered(
    query_embedding VECTOR,
    match_count INT,
    p_unique_names TEXT[]
)
RETURNS TABLE (
    id BIGINT,
    unique_name TEXT,
    chunk_id INTEGER,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.unique_name,
        e.chunk_id,
        e.content,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM
        embeddings e
    WHERE
        e.unique_name = ANY(p_unique_names)
    ORDER BY
        e.embedding <=> query_embedding
    LIMIT match_count;

END;

$$;

-- End of migration file: 01_initial_schema.sql

-- Project URLs table
CREATE TABLE IF NOT EXISTS project_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- End of migration file: 02_project_urls_table.sql

-- Add formatted_tabular_data field to scrape_sessions table
ALTER TABLE IF EXISTS scrape_sessions
ADD COLUMN IF NOT EXISTS formatted_tabular_data JSONB;

-- Add display_format field to scrape_sessions table
ALTER TABLE IF EXISTS scrape_sessions
ADD COLUMN IF NOT EXISTS display_format TEXT DEFAULT 'table';

-- Add comment to explain the purpose of the formatted_tabular_data field
COMMENT ON COLUMN scrape_sessions.formatted_tabular_data IS 'Stores the formatted tabular data for different display formats (table, paragraph, raw)';

-- Add comment to explain the purpose of the display_format field
COMMENT ON COLUMN scrape_sessions.display_format IS 'Stores the display format preference for this session (table, paragraph, raw)';

-- End of migration file: 03_add_formatted_tabular_data.sql

-- Add caching_enabled field to projects table
ALTER TABLE IF EXISTS projects
ADD COLUMN IF NOT EXISTS caching_enabled BOOLEAN NOT NULL DEFAULT TRUE;

-- Add comment to explain the purpose of the caching_enabled field
COMMENT ON COLUMN projects.caching_enabled IS 'Controls whether web scraping should use cached content or always fetch fresh content';

-- End of migration file: 04_add_caching_enabled.sql

ALTER TABLE project_urls ADD COLUMN rag_enabled BOOLEAN DEFAULT FALSE;

-- End of migration file: 05_add_rag_enabled_to_project_urls.sql

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

-- End of migration file: create_project_urls_table.sql;

