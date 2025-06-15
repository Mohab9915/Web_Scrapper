-- Migration: Fix existing scrape_sessions and project_urls to have correct user_id
-- This migration updates existing records to have the correct user_id based on project ownership

-- Update scrape_sessions to have user_id from their associated project
UPDATE scrape_sessions 
SET user_id = projects.user_id
FROM projects 
WHERE scrape_sessions.project_id = projects.id 
AND scrape_sessions.user_id IS NULL;

-- Update project_urls to have user_id from their associated project
UPDATE project_urls 
SET user_id = projects.user_id
FROM projects 
WHERE project_urls.project_id = projects.id 
AND project_urls.user_id IS NULL;

-- Update markdowns to have user_id based on the scrape_sessions they belong to
-- First, we need to find the relationship between markdowns and sessions
-- The unique_name in markdowns corresponds to unique_scrape_identifier in sessions
UPDATE markdowns 
SET user_id = scrape_sessions.user_id
FROM scrape_sessions 
WHERE markdowns.unique_name = scrape_sessions.unique_scrape_identifier 
AND markdowns.user_id IS NULL;

-- Update embeddings to have user_id based on the scrape_sessions they belong to
-- The unique_name in embeddings corresponds to unique_scrape_identifier in sessions
UPDATE embeddings 
SET user_id = scrape_sessions.user_id
FROM scrape_sessions 
WHERE embeddings.unique_name = scrape_sessions.unique_scrape_identifier 
AND embeddings.user_id IS NULL;

-- Add a comment to track this migration
COMMENT ON TABLE scrape_sessions IS 'Updated existing records with correct user_id from project ownership - Migration 11';
