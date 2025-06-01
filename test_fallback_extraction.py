#!/usr/bin/env python3
"""
Test the updated fallback extraction with user-focused field mapping
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.append('backend')

async def test_fallback_extraction():
    """Test the updated fallback extraction method"""
    
    try:
        # We're already in backend directory, just fix imports
        sys.path.insert(0, '.')
        
        from app.services.scraping_service import ScrapingService
        
        print("🧪 Testing Updated Fallback Extraction")
        print("=" * 60)
        
        # Create a sample markdown content similar to scrapethissite.com
        sample_markdown = """
# Countries

### Andorra
**Capital:** Andorra la Vella
**Population:** 84000
**Area (km2):** 468.0

### Afghanistan  
**Capital:** Kabul
**Population:** 29121286
**Area (km2):** 647500

### Albania
**Capital:** Tirana
**Population:** 2986952
**Area (km2):** 28748
"""
        
        # Test with user-requested fields: "name, area"
        test_fields = ["name", "area"]
        
        print(f"📋 Test Fields: {test_fields}")
        print(f"📝 Sample Content Length: {len(sample_markdown)} chars")
        
        # Create scraping service instance
        scraping_service = ScrapingService()
        
        # Test the fallback extraction
        structured_data, tabular_data = await scraping_service._extract_data_fallback(sample_markdown, test_fields)
        
        print(f"\n📊 Extraction Results:")
        print(f"   Method: {structured_data.get('extraction_method', 'Not specified')}")
        print(f"   Total Items: {structured_data.get('total_items', 'Not specified')}")
        print(f"   Requested Fields: {structured_data.get('requested_fields', 'Not specified')}")
        
        if tabular_data and len(tabular_data) > 0:
            print(f"\n🔍 First Item:")
            first_item = tabular_data[0]
            for key, value in first_item.items():
                print(f"   {key}: \"{value}\"")
            
            print(f"\n🔍 Available Fields: {list(first_item.keys())}")
            
            # Check if user-requested fields are present
            for field in test_fields:
                if field in first_item:
                    print(f"✅ Field '{field}' found with value: \"{first_item[field]}\"")
                else:
                    print(f"❌ Field '{field}' missing!")
            
            # Check for unwanted extra fields
            extra_fields = [f for f in first_item.keys() if f not in test_fields]
            if extra_fields:
                print(f"⚠️  Extra fields found: {extra_fields}")
            else:
                print(f"✅ No extra fields - only requested fields present")
                
        else:
            print(f"❌ No tabular data extracted")
        
        print(f"\n✅ Fallback extraction test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fallback_extraction())
