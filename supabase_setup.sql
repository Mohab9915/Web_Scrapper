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

