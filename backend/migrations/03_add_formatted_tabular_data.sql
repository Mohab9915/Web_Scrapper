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
