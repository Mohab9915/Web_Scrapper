#!/usr/bin/env python3
"""
Fix existing session data to use user-requested field names
"""

import sys
import os
import json

# Add backend to path
sys.path.append('backend')

def fix_existing_session_data():
    """Fix the existing session data to map country -> name"""
    
    try:
        # We're already in backend directory, just fix imports
        sys.path.insert(0, '.')
        
        from app.database import supabase
        
        print("🔧 Fixing Existing Session Data")
        print("=" * 50)
        
        # Find the latest session for the countries project
        session = supabase.table('scrape_sessions').select('*').eq('id', '800ae11c-3900-4bb0-a7d4-6dc575d079ef').single().execute()
        
        if not session.data:
            print("❌ Session not found")
            return
            
        session_data = session.data
        print(f"📋 Session: {session_data['id']}")
        print(f"🌐 URL: {session_data['url']}")
        
        # Get the structured data
        structured_data = json.loads(session_data['structured_data_json'])
        print(f"📊 Original extraction method: {structured_data.get('extraction_method', 'Not specified')}")
        
        if 'listings' in structured_data:
            listings = structured_data['listings']
            print(f"📋 Total items: {len(listings)}")
            
            if listings and len(listings) > 0:
                print(f"🔍 Original first item keys: {list(listings[0].keys())}")
                
                # Fix the field mapping: country -> name
                fixed_listings = []
                for item in listings:
                    fixed_item = {}
                    
                    # Map country to name (user requested "name")
                    if 'country' in item:
                        fixed_item['name'] = item['country']
                    
                    # Keep area as requested
                    if 'area' in item:
                        fixed_item['area'] = item['area']
                    
                    # Don't include other fields since user only requested "name, area"
                    fixed_listings.append(fixed_item)
                
                # Update the structured data
                structured_data['listings'] = fixed_listings
                structured_data['extraction_method'] = 'fixed_user_focused_mapping'
                structured_data['requested_fields'] = ['name', 'area']
                structured_data['total_items'] = len(fixed_listings)
                
                print(f"🔍 Fixed first item keys: {list(fixed_listings[0].keys())}")
                print(f"🔍 Fixed first item: {fixed_listings[0]}")
                
                # Update the session in database
                update_response = supabase.table('scrape_sessions').update({
                    'structured_data_json': json.dumps(structured_data)
                }).eq('id', session_data['id']).execute()
                
                if update_response.data:
                    print("✅ Session data updated successfully")
                    
                    # Also update the formatted_tabular_data if it exists
                    if session_data.get('formatted_tabular_data'):
                        try:
                            formatted_data = json.loads(session_data['formatted_tabular_data'])
                            if 'listings' in formatted_data:
                                formatted_data['listings'] = fixed_listings
                                
                                supabase.table('scrape_sessions').update({
                                    'formatted_tabular_data': json.dumps(formatted_data)
                                }).eq('id', session_data['id']).execute()
                                
                                print("✅ Formatted data also updated")
                        except Exception as e:
                            print(f"⚠️  Could not update formatted data: {e}")
                else:
                    print("❌ Failed to update session data")
            else:
                print("❌ No listings found in structured data")
        else:
            print("❌ No listings key found in structured data")
        
        print(f"\n✅ Session data fix completed!")
        
    except Exception as e:
        print(f"❌ Error during fix: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_existing_session_data()
