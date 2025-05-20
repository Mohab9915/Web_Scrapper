-- Add caching_enabled field to projects table
ALTER TABLE IF EXISTS projects
ADD COLUMN IF NOT EXISTS caching_enabled BOOLEAN NOT NULL DEFAULT TRUE;

-- Add comment to explain the purpose of the caching_enabled field
COMMENT ON COLUMN projects.caching_enabled IS 'Controls whether web scraping should use cached content or always fetch fresh content';
