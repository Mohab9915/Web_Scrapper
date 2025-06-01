-- Add SQL function to get conversation summaries for a project
CREATE OR REPLACE FUNCTION get_project_conversations_summary(
    p_project_id UUID,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    conversation_id UUID,
    last_message_at TIMESTAMPTZ,
    preview TEXT,
    message_count BIGINT,
    title TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH conversation_stats AS (
        SELECT
            ch.conversation_id,
            MAX(ch.created_at) as last_message_at,
            COUNT(*) as message_count,
            -- Get the first user message as preview
            (
                SELECT ch2.message_content
                FROM chat_history ch2
                WHERE ch2.conversation_id = ch.conversation_id
                AND ch2.message_role = 'user'
                ORDER BY ch2.created_at ASC
                LIMIT 1
            ) as first_user_message,
            -- Get conversation title from system message metadata
            (
                SELECT ch3.metadata->>'conversation_title'
                FROM chat_history ch3
                WHERE ch3.conversation_id = ch.conversation_id
                AND ch3.message_role = 'system'
                AND ch3.metadata ? 'conversation_title'
                ORDER BY ch3.created_at DESC
                LIMIT 1
            ) as conversation_title
        FROM chat_history ch
        WHERE ch.project_id = p_project_id
        GROUP BY ch.conversation_id
    )
    SELECT
        cs.conversation_id,
        cs.last_message_at,
        CASE
            WHEN LENGTH(cs.first_user_message) > 100
            THEN LEFT(cs.first_user_message, 100) || '...'
            ELSE COALESCE(cs.first_user_message, 'No user messages')
        END as preview,
        cs.message_count,
        cs.conversation_title as title
    FROM conversation_stats cs
    ORDER BY cs.last_message_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
