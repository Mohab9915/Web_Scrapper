import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database import supabase

# Query scrape_sessions table
sessions = supabase.table('scrape_sessions').select('*').execute()

# Print the number of sessions
print(f"Number of scraping sessions: {len(sessions.data)}")

# Print session details if any exist
if sessions.data:
    print("\nScraping Sessions:")
    for i, session in enumerate(sessions.data, 1):
        print(f"\nSession {i}:")
        print(f"  ID: {session.get('id')}")
        print(f"  Project ID: {session.get('project_id')}")
        print(f"  URL: {session.get('url')}")
        print(f"  Status: {session.get('status')}")
        print(f"  Created at: {session.get('scraped_at')}")
else:
    print("\nNo scraping sessions found in the database.")

# Query web_cache table
cache = supabase.table('web_cache').select('*').execute()

# Print the number of cached pages
print(f"\nNumber of cached web pages: {len(cache.data)}")

# Print cache details if any exist
if cache.data:
    print("\nCached Web Pages:")
    for i, entry in enumerate(cache.data, 1):
        print(f"\nCache Entry {i}:")
        print(f"  URL: {entry.get('url')}")
        print(f"  Created at: {entry.get('created_at')}")
        print(f"  Expires at: {entry.get('expires_at')}")
        print(f"  Hit count: {entry.get('cache_hit_count')}")
else:
    print("\nNo cached web pages found in the database.")
