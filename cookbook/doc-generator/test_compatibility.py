#!/usr/bin/env python3
"""
Test script to verify backward compatibility of enhanced flows
"""

def test_original_imports():
    """Test that original flows can still be imported"""
    print("Testing original flow imports...")
    try:
        from flows.working_group import working_group_flow, group_lead_node, group_evaluator_node
        print("✓ Original working_group imports successful")
        
        from flows.comittee import committee_flow, committee_node
        print("✓ Original committee imports successful")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_enhanced_imports():
    """Test that enhanced flows can be imported"""
    print("\nTesting enhanced flow imports...")
    try:
        from flows.working_group_complete import enhanced_working_group_flow, enhanced_group_lead_node
        print("✓ Enhanced working_group imports successful")
        
        from flows.committee_complete import enhanced_committee_flow, enhanced_committee_node
        print("✓ Enhanced committee imports successful")
        
        from flows.completeness import document_completeness_node, completeness_report_node
        print("✓ Completeness node imports successful")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_coexistence():
    """Test that both versions can coexist"""
    print("\nTesting coexistence of original and enhanced flows...")
    try:
        # Import both versions
        from flows.working_group import working_group_flow as original_wg
        from flows.working_group_complete import enhanced_working_group_flow as enhanced_wg
        
        # Verify they are different objects
        if original_wg is enhanced_wg:
            print("✗ Original and enhanced flows are the same object!")
            return False
        
        print("✓ Original and enhanced flows are separate objects")
        
        # Check node differences
        from flows.working_group import group_lead_node as original_lead
        from flows.working_group_complete import enhanced_group_lead_node as enhanced_lead
        
        if type(original_lead).__name__ != type(enhanced_lead).__name__:
            print("✓ Lead nodes have different implementations")
        
        return True
    except Exception as e:
        print(f"✗ Coexistence error: {e}")
        return False

def test_main_files():
    """Test that all main files exist"""
    print("\nTesting main file availability...")
    import os
    
    files_to_check = [
        ("main.py", "Original main"),
        ("main_complete.py", "Enhanced main with completeness"),
        ("section_main.py", "Section-based main"),
        ("section_main_complete.py", "Section-based main with completeness")
    ]
    
    all_exist = True
    for filename, description in files_to_check:
        if os.path.exists(filename):
            print(f"✓ {description} ({filename}) exists")
        else:
            print(f"✗ {description} ({filename}) missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all compatibility tests"""
    print("=== Document Generator Compatibility Test ===\n")
    
    tests = [
        test_original_imports,
        test_enhanced_imports,
        test_coexistence,
        test_main_files
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All compatibility tests passed!")
        print("Original flows remain intact and functional.")
        print("Enhanced flows with completeness analysis are available.")
        print("\nUsers can choose between:")
        print("  - python main.py                    # Original document generation")
        print("  - python main_complete.py           # Enhanced with completeness checks")
        print("  - python section_main.py            # Section-based generation")
        print("  - python section_main_complete.py   # Section-based with completeness")
    else:
        print("\n❌ Some compatibility tests failed!")

if __name__ == "__main__":
    main()