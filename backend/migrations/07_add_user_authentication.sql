-- Migration: Add user authentication and Row Level Security (RLS)
-- This migration adds user_id columns to existing tables and sets up RLS policies

-- First, add user_id columns to existing tables that don't have them yet
-- Note: These ALTER TABLE statements will only run if the columns don't exist

-- Add user_id to projects table (if not already added)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='projects' AND column_name='user_id') THEN
        ALTER TABLE projects ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add user_id to project_urls table (if not already added)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='project_urls' AND column_name='user_id') THEN
        ALTER TABLE project_urls ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add user_id to scrape_sessions table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scrape_sessions' AND column_name='user_id') THEN
        ALTER TABLE scrape_sessions ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add user_id to markdowns table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='markdowns' AND column_name='user_id') THEN
        ALTER TABLE markdowns ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add user_id to embeddings table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='embeddings' AND column_name='user_id') THEN
        ALTER TABLE embeddings ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Add user_id to chat_history table (if not already added)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='chat_history' AND column_name='user_id') THEN
        ALTER TABLE chat_history ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_urls ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE markdowns ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for projects table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'projects' AND policyname = 'Users can only access their own projects') THEN
        CREATE POLICY "Users can only access their own projects" ON projects
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create RLS policies for project_urls table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'project_urls' AND policyname = 'Users can only access their own project URLs') THEN
        CREATE POLICY "Users can only access their own project URLs" ON project_urls
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create RLS policies for scrape_sessions table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'scrape_sessions' AND policyname = 'Users can only access their own scrape sessions') THEN
        CREATE POLICY "Users can only access their own scrape sessions" ON scrape_sessions
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create RLS policies for markdowns table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'markdowns' AND policyname = 'Users can only access their own markdowns') THEN
        CREATE POLICY "Users can only access their own markdowns" ON markdowns
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create RLS policies for embeddings table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'embeddings' AND policyname = 'Users can only access their own embeddings') THEN
        CREATE POLICY "Users can only access their own embeddings" ON embeddings
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create RLS policies for chat_history table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'chat_history' AND policyname = 'Users can only access their own chat history') THEN
        CREATE POLICY "Users can only access their own chat history" ON chat_history
            FOR ALL USING (auth.uid() = user_id);
    END IF;
END $$;

-- Update the match_embeddings_filtered function to include user filtering
CREATE OR REPLACE FUNCTION match_embeddings_filtered(
    query_embedding VECTOR,
    match_count INT,
    p_unique_names TEXT[],
    p_user_id UUID DEFAULT NULL
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
        AND (p_user_id IS NULL OR e.user_id = p_user_id)
    ORDER BY
        e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create indexes for better performance on user_id columns
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_project_urls_user_id ON project_urls(user_id);
CREATE INDEX IF NOT EXISTS idx_scrape_sessions_user_id ON scrape_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_markdowns_user_id ON markdowns(user_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_user_id ON embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);

-- Create a function to automatically set user_id on insert
CREATE OR REPLACE FUNCTION set_user_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.user_id = auth.uid();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create triggers to automatically set user_id on insert for tables that need it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_id_projects') THEN
        CREATE TRIGGER set_user_id_projects
            BEFORE INSERT ON projects
            FOR EACH ROW
            WHEN (NEW.user_id IS NULL)
            EXECUTE FUNCTION set_user_id();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_id_project_urls') THEN
        CREATE TRIGGER set_user_id_project_urls
            BEFORE INSERT ON project_urls
            FOR EACH ROW
            WHEN (NEW.user_id IS NULL)
            EXECUTE FUNCTION set_user_id();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_id_scrape_sessions') THEN
        CREATE TRIGGER set_user_id_scrape_sessions
            BEFORE INSERT ON scrape_sessions
            FOR EACH ROW
            WHEN (NEW.user_id IS NULL)
            EXECUTE FUNCTION set_user_id();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_id_markdowns') THEN
        CREATE TRIGGER set_user_id_markdowns
            BEFORE INSERT ON markdowns
            FOR EACH ROW
            WHEN (NEW.user_id IS NULL)
            EXECUTE FUNCTION set_user_id();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_id_embeddings') THEN
        CREATE TRIGGER set_user_id_embeddings
            BEFORE INSERT ON embeddings
            FOR EACH ROW
            WHEN (NEW.user_id IS NULL)
            EXECUTE FUNCTION set_user_id();
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_user_id_chat_history') THEN
        CREATE TRIGGER set_user_id_chat_history
            BEFORE INSERT ON chat_history
            FOR EACH ROW
            WHEN (NEW.user_id IS NULL)
            EXECUTE FUNCTION set_user_id();
    END IF;
END $$;
