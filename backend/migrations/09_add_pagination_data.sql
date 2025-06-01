-- Add pagination_data field to scrape_sessions table
ALTER TABLE IF EXISTS scrape_sessions
ADD COLUMN IF NOT EXISTS pagination_data JSONB;

-- Add comment to explain the purpose of the pagination_data field
COMMENT ON COLUMN scrape_sessions.pagination_data IS 'Stores pagination data extracted from the scraped page';
