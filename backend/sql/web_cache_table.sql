-- Create web_cache table for caching web pages
CREATE TABLE IF NOT EXISTS web_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL UNIQUE,
    content JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    cache_hit_count INTEGER NOT NULL DEFAULT 0,
    
    -- Create index on URL for faster lookups
    CONSTRAINT web_cache_url_idx UNIQUE (url)
);

-- Create index on expiration time for cleanup operations
CREATE INDEX IF NOT EXISTS web_cache_expires_at_idx ON web_cache (expires_at);

-- Create function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache() RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM web_cache WHERE expires_at < NOW();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to clean expired cache entries periodically
DROP TRIGGER IF EXISTS clean_expired_cache_trigger ON web_cache;
CREATE TRIGGER clean_expired_cache_trigger
AFTER INSERT ON web_cache
EXECUTE PROCEDURE clean_expired_cache();

-- Add RLS policies
ALTER TABLE web_cache ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users
CREATE POLICY web_cache_policy ON web_cache
    USING (true)
    WITH CHECK (true);
