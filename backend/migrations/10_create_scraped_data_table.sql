-- Create the missing scraped_data table that is being referenced in the logs
-- This table appears to be expected by some part of the scraping pipeline

CREATE TABLE IF NOT EXISTS scraped_data (
    id BIGSERIAL PRIMARY KEY,
    unique_name TEXT NOT NULL UNIQUE,
    url TEXT,
    data JSONB,
    pagination_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add index for performance on the unique_name field (used in upsert operations)
CREATE INDEX IF NOT EXISTS scraped_data_unique_name_idx ON scraped_data(unique_name);

-- Add index for URL lookups
CREATE INDEX IF NOT EXISTS scraped_data_url_idx ON scraped_data(url);

-- Add index for created_at for time-based queries
CREATE INDEX IF NOT EXISTS scraped_data_created_at_idx ON scraped_data(created_at);

-- Add comment to explain the purpose of this table
COMMENT ON TABLE scraped_data IS 'Stores scraped data with pagination information. This table is used by the scraping pipeline for data that requires pagination handling.';

COMMENT ON COLUMN scraped_data.unique_name IS 'Unique identifier for the scraped data entry, used for upsert operations';
COMMENT ON COLUMN scraped_data.url IS 'Source URL of the scraped data';
COMMENT ON COLUMN scraped_data.data IS 'JSON data containing the scraped content';
COMMENT ON COLUMN scraped_data.pagination_data IS 'JSON data containing pagination information for multi-page scraping';
