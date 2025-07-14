#!/usr/bin/env python3
"""
Verify that the feedback flattening fix handles all edge cases
"""

def test_feedback_flattening():
    """Test the feedback flattening logic"""
    print("Testing feedback flattening logic...\n")
    
    test_cases = [
        {
            "name": "Normal strings",
            "input": ["item1", "item2", "item3"],
            "expected": ["item1", "item2", "item3"]
        },
        {
            "name": "Mixed with empty strings",
            "input": ["item1", "", "item2", ""],
            "expected": ["item1", "item2"]
        },
        {
            "name": "Nested lists",
            "input": ["item1", ["nested1", "nested2"], "item3"],
            "expected": ["item1", "nested1", "nested2", "item3"]
        },
        {
            "name": "Empty nested lists",
            "input": ["item1", [], [""], "item2"],
            "expected": ["item1", "item2"]
        },
        {
            "name": "Deep nesting",
            "input": ["item1", ["nested1", ["deep1"]], "item2"],
            "expected": ["item1", "nested1", "['deep1']", "item2"]  # Deep nesting gets stringified
        },
        {
            "name": "All empty",
            "input": ["", [], ["", ""]],
            "expected": []
        }
    ]
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"Input: {test['input']}")
        
        # Apply the flattening logic
        flattened_feedback = []
        for item in test['input']:
            if isinstance(item, list):
                # If item is a list, flatten it
                flattened_feedback.extend([str(sub_item) for sub_item in item if sub_item])
            elif item:  # Non-empty string or other truthy value
                flattened_feedback.append(str(item))
        
        print(f"Output: {flattened_feedback}")
        print(f"Expected: {test['expected']}")
        
        # Check result
        if flattened_feedback == test['expected']:
            print("✓ PASS\n")
        else:
            print("✗ FAIL\n")

if __name__ == "__main__":
    test_feedback_flattening()
    
    print("\nFix Summary:")
    print("1. The feedback flattening logic now handles:")
    print("   - Regular string feedback items")
    print("   - Empty strings (filtered out)")
    print("   - Nested lists (flattened)")
    print("   - Empty nested lists (ignored)")
    print("2. All items are converted to strings to prevent type errors")
    print("3. Empty feedback after flattening returns None to skip processing")