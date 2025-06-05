-- Chat History table for storing conversation messages (updated with user_id)
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES scrape_sessions(id) ON DELETE SET NULL, -- Optional: link to specific scrape session
    conversation_id UUID NOT NULL, -- Groups messages into conversations
    message_role TEXT NOT NULL CHECK (message_role IN ('user', 'assistant', 'system')),
    message_content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- Store additional data like cost, sources, model_used, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS chat_history_project_id_idx ON chat_history(project_id);
CREATE INDEX IF NOT EXISTS chat_history_session_id_idx ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS chat_history_conversation_id_idx ON chat_history(conversation_id);
CREATE INDEX IF NOT EXISTS chat_history_created_at_idx ON chat_history(created_at);

-- Add composite index for project + conversation queries
CREATE INDEX IF NOT EXISTS chat_history_project_conversation_idx ON chat_history(project_id, conversation_id, created_at);

-- Add RLS policies for security
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (you can restrict this further based on your auth system)
CREATE POLICY chat_history_policy ON chat_history
    USING (true)
    WITH CHECK (true);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_chat_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_chat_history_updated_at
    BEFORE UPDATE ON chat_history
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_history_updated_at();

-- Comments to document the table structure
COMMENT ON TABLE chat_history IS 'Stores chat conversation messages between users and the RAG system';
COMMENT ON COLUMN chat_history.project_id IS 'References the project this conversation belongs to';
COMMENT ON COLUMN chat_history.session_id IS 'Optional reference to a specific scrape session';
COMMENT ON COLUMN chat_history.conversation_id IS 'Groups related messages into a conversation thread';
COMMENT ON COLUMN chat_history.message_role IS 'Role of the message sender: user, assistant, or system';
COMMENT ON COLUMN chat_history.message_content IS 'The actual message text content';
COMMENT ON COLUMN chat_history.metadata IS 'JSON field storing additional data like cost, sources, model_used, etc.';
