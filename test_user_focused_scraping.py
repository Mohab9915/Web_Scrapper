#!/usr/bin/env python3
"""
Test the user-focused scraping fix
"""

import sys
import os

# Add backend to path
sys.path.append('backend')

def test_user_focused_system_message():
    """Test the new user-focused system message generation"""
    
    try:
        # We're already in backend directory, just fix imports
        sys.path.insert(0, '.')

        from app.scraper_modules.assets import generate_user_focused_system_message
        
        print("🧪 Testing User-Focused System Message Generation")
        print("=" * 60)
        
        # Test with user conditions: "name, area"
        test_fields = ["name", "area"]
        system_message = generate_user_focused_system_message(test_fields)
        
        print(f"📋 Test Fields: {test_fields}")
        print(f"📝 Generated System Message:")
        print("-" * 40)
        print(system_message)
        print("-" * 40)
        
        # Check if the message contains the key instructions
        key_phrases = [
            "USER REQUESTED FIELDS: name, area",
            "ONLY extract data for these exact fields",
            "Do NOT add any additional fields",
            "use the exact field names provided by the user",
            "map \"country\" data to the \"name\" field"
        ]
        
        print(f"\n🔍 Checking for key phrases:")
        for phrase in key_phrases:
            if phrase in system_message:
                print(f"✅ Found: '{phrase}'")
            else:
                print(f"❌ Missing: '{phrase}'")
        
        print(f"\n✅ User-focused system message generation test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_focused_system_message()
