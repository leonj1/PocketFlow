#!/usr/bin/env python3
"""Test script to verify workflow runs without stopping after context load."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from document_workflow import DocumentWorkflow
import datetime

# Mock input to avoid interactive prompts
class MockInput:
    def __init__(self, responses):
        self.responses = iter(responses)
    
    def __call__(self, prompt):
        try:
            return next(self.responses)
        except StopIteration:
            return "n"  # Default to 'n' for any unexpected prompts

# Monkey patch input
import builtins
builtins.input = MockInput([
    "2",  # No additional needs
    "2",  # Don't save audit trail
])

def test_workflow():
    """Test that workflow progresses past context loading."""
    print("Testing workflow progression...")
    print("="*60)
    
    shared_state = {
        "workflow_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "start_time": datetime.datetime.now().isoformat()
    }
    
    workflow = DocumentWorkflow("context.yml")
    
    # The workflow should not stop after context loading
    # It should continue through needs assessment
    result = workflow.run(shared_state)
    
    # Check that we progressed past context loading
    if "context" in shared_state:
        print("✓ Context loaded successfully")
    
    if "assessed_needs" in shared_state.get("document", {}):
        print("✓ Needs assessment completed")
        print("✓ Workflow progressed past context loading!")
        return True
    else:
        print("✗ Workflow stopped after context loading")
        return False

if __name__ == "__main__":
    success = test_workflow()
    sys.exit(0 if success else 1)