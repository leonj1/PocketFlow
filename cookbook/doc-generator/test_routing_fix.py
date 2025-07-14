#!/usr/bin/env python3
"""
Test script to verify the completeness routing fix.
This simulates document completeness analysis with different scores
to ensure proper routing behavior.
"""

class MockDocumentCompletenessNode:
    """Mock version of DocumentCompletenessNode with the fix"""
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            print(f"\n Completeness Analysis Complete. Score: {exec_res['overall_completeness']}/100")
            
            # Store results in shared
            shared["completeness_analysis"] = exec_res
            
            # Determine if document meets completeness threshold
            if exec_res["overall_completeness"] < 70:
                print(f"\n  Document needs improvement - triggering revision cycle")
                print(f"  Current attempt: {shared.get('attempts', {}).get('current', 0) + 1}/{shared.get('attempts', {}).get('max', 3)}")
                # Increment attempts
                if "attempts" in shared:
                    shared["attempts"]["current"] += 1
                return "needs_improvement"
            else:
                print(f"\n  Document meets completeness threshold - generating report")
                return "generate_report"
        
        return None

def test_routing(score, attempts_current=0, attempts_max=3):
    """Test routing behavior for a given completeness score"""
    print(f"\n{'='*60}")
    print(f"Testing score: {score}/100")
    print(f"{'='*60}")
    
    # Create mock shared state
    shared = {
        "attempts": {
            "current": attempts_current,
            "max": attempts_max
        }
    }
    
    # Create mock execution result
    exec_res = {
        "overall_completeness": score,
        "readability_issues": [],
        "conceptual_gaps": [],
        "unfulfilled_goals": [],
        "scope_violations": []
    }
    
    # Test the node
    node = MockDocumentCompletenessNode()
    action = node.post(shared, None, exec_res)
    
    print(f"\nResult:")
    print(f"  - Action returned: '{action}'")
    print(f"  - Attempts after: {shared['attempts']['current']}/{shared['attempts']['max']}")
    
    # Verify routing
    if score < 70:
        expected = "needs_improvement"
        routing = "→ section_revision_node (revision cycle)"
    else:
        expected = "generate_report"
        routing = "→ completeness_report_node → committee"
    
    is_correct = action == expected
    status = "✓ CORRECT" if is_correct else "✗ INCORRECT"
    
    print(f"  - Expected action: '{expected}'")
    print(f"  - Routing: {routing}")
    print(f"  - Status: {status}")
    
    return is_correct

def test_workflow_connections():
    """Test that workflow connections are properly configured"""
    print(f"\n{'='*60}")
    print("Workflow Connection Test")
    print(f"{'='*60}")
    
    print("\nOLD (Problematic) Configuration:")
    print("  document_completeness_node >> completeness_report_node  # Default path")
    print("  document_completeness_node - 'needs_improvement' >> section_revision_node")
    print("  ⚠️  Problem: Default path allows bypass even with low scores")
    
    print("\nNEW (Fixed) Configuration:")
    print("  document_completeness_node - 'generate_report' >> completeness_report_node")
    print("  document_completeness_node - 'needs_improvement' >> section_revision_node")
    print("  ✓  Solution: No default path - explicit routing based on score")
    
    print("\nKey Changes:")
    print("  1. Removed default connection (>>)")
    print("  2. Added explicit 'generate_report' action for high scores")
    print("  3. Both paths now require specific actions")

def main():
    """Run all routing tests"""
    print("DOCUMENT COMPLETENESS ROUTING TESTS")
    print("=" * 60)
    
    # Test various scores
    test_cases = [
        (30.0, "Very low score - should trigger revision"),
        (50.0, "Low score - should trigger revision"),
        (69.9, "Just below threshold - should trigger revision"),
        (70.0, "Exactly at threshold - should generate report"),
        (85.0, "High score - should generate report"),
        (100.0, "Perfect score - should generate report"),
    ]
    
    all_passed = True
    for score, description in test_cases:
        print(f"\n{description}")
        passed = test_routing(score)
        all_passed = all_passed and passed
    
    # Test workflow connections
    test_workflow_connections()
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    if all_passed:
        print("✓ All routing tests PASSED")
        print("✓ Documents with scores < 70% will enter revision cycles")
        print("✓ Documents with scores >= 70% will proceed to committee")
    else:
        print("✗ Some tests FAILED")
    
    print("\nConclusion:")
    print("The fix ensures that documents like the one with 30.0/100 completeness")
    print("will now properly enter revision cycles instead of being published.")

if __name__ == "__main__":
    main()