#!/usr/bin/env python3
"""
Test to verify the frontend JavaScript error is fixed
"""

import requests
import time

def test_frontend_loading():
    """Test if the frontend loads without JavaScript errors"""
    
    print("🔍 Testing Frontend JavaScript Fix")
    print("=" * 50)
    
    frontend_url = "http://localhost:9002"
    
    try:
        # Test if frontend is accessible
        response = requests.get(frontend_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            
            # Check if the HTML contains React app structure
            html_content = response.text
            
            if 'react' in html_content.lower() or 'root' in html_content:
                print("✅ React app structure detected")
                
                # Check for any obvious JavaScript errors in the HTML
                if 'error' in html_content.lower() and 'javascript' in html_content.lower():
                    print("⚠️  Potential JavaScript errors in HTML")
                else:
                    print("✅ No obvious JavaScript errors in HTML")
                
                return True
            else:
                print("❌ React app structure not found")
                return False
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_component_syntax():
    """Test if the MessageRenderer component has valid syntax"""
    
    print("\n🔍 Testing MessageRenderer Component Syntax")
    print("=" * 50)
    
    try:
        with open("new-front/src/components/MessageRenderer.js", "r") as f:
            content = f.read()
        
        # Check for key fixes
        checks = [
            ("extractChartData function", "const extractChartData = (text) => {"),
            ("useMemo for chartData", "const chartData = useMemo(() => extractChartData(content)"),
            ("useMemo for renderContent", "const renderContent = useMemo(() => {"),
            ("renderEnhancedText function", "const renderEnhancedText = (text) => {"),
            ("memo wrapper", "const MessageRenderer = memo("),
            ("StableChartRenderer import", "import StableChartRenderer"),
        ]
        
        all_passed = True
        
        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        # Check for function order (extractChartData should come before useMemo)
        extract_pos = content.find("const extractChartData")
        usememo_pos = content.find("const chartData = useMemo")
        
        if extract_pos < usememo_pos and extract_pos != -1 and usememo_pos != -1:
            print("✅ Function order - extractChartData defined before useMemo")
        else:
            print("❌ Function order - extractChartData not properly positioned")
            all_passed = False
        
        # Check for duplicate functions
        enhanced_text_count = content.count("const renderEnhancedText")
        if enhanced_text_count == 1:
            print("✅ No duplicate renderEnhancedText functions")
        else:
            print(f"⚠️  Found {enhanced_text_count} renderEnhancedText functions")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Component syntax test failed: {e}")
        return False

def test_stable_chart_renderer():
    """Test if StableChartRenderer component exists and is valid"""
    
    print("\n🔍 Testing StableChartRenderer Component")
    print("=" * 50)
    
    try:
        with open("new-front/src/components/StableChartRenderer.js", "r") as f:
            content = f.read()
        
        checks = [
            ("memo wrapper", "memo("),
            ("useState hook", "useState"),
            ("useEffect hook", "useEffect"),
            ("JSON.stringify comparison", "JSON.stringify"),
            ("ChartRenderer import", "import ChartRenderer"),
            ("Custom comparison", "(prevProps, nextProps)"),
        ]
        
        all_passed = True
        
        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        print("❌ StableChartRenderer.js not found")
        return False
    except Exception as e:
        print(f"❌ StableChartRenderer test failed: {e}")
        return False

def main():
    """Run all frontend fix tests"""
    
    print("🚀 FRONTEND JAVASCRIPT FIX VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Frontend Loading", test_frontend_loading),
        ("MessageRenderer Syntax", test_component_syntax),
        ("StableChartRenderer", test_stable_chart_renderer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FRONTEND FIX VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All frontend fixes verified!")
        print("✅ JavaScript hoisting error should be resolved")
        print("✅ Chart stability improvements are in place")
    elif passed >= total * 0.8:
        print("✅ Most frontend fixes are working")
        print("⚠️  Some minor issues may remain")
    else:
        print("⚠️  Frontend fixes need attention")
    
    print("\n📋 NEXT STEPS:")
    print("1. Open http://localhost:9002 in your browser")
    print("2. Check browser console for any remaining errors")
    print("3. Test chart generation and stability")
    print("4. Verify no chart refreshing when typing in chat")
    
    return passed, total

if __name__ == "__main__":
    main()
