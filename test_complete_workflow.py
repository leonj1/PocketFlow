#!/usr/bin/env python3
"""Test script to run the complete workflow and track progress."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from document_workflow import DocumentWorkflow
import datetime

# Mock input to avoid interactive prompts
class MockInput:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.current_prompt = ""
    
    def __call__(self, prompt):
        self.current_prompt = prompt
        print(f"[MOCK INPUT] Prompt: {prompt}")
        try:
            response = next(self.responses)
            print(f"[MOCK INPUT] Response: {response}")
            return response
        except StopIteration:
            print("[MOCK INPUT] No more responses, defaulting to 'n'")
            return "n"

# Monkey patch input with a comprehensive set of responses
import builtins
builtins.input = MockInput([
    "2",  # No additional needs (needs assessment)
    "1",  # Approve (peer review)
    "",   # No additional comments
    "1",  # Approve (working group)
    "",   # No additional comments
    "1",  # Approve (committee review)
    "",   # No additional comments
    "1",  # Approve (committee approval)
    "1",  # Yes - unanimous approval
    "1",  # Complete training
    "1",  # Active maintenance
    "2",  # Don't save audit trail
])

def test_complete_workflow():
    """Test that workflow runs through all stages."""
    print("Testing complete workflow execution...")
    print("="*60)
    
    shared_state = {
        "workflow_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "start_time": datetime.datetime.now().isoformat()
    }
    
    workflow = DocumentWorkflow("context.yml")
    
    # Run the workflow
    result = workflow.run(shared_state)
    
    print("\n" + "="*60)
    print("WORKFLOW EXECUTION SUMMARY")
    print("="*60)
    
    # Check progress through stages
    stages_completed = []
    
    if "context" in shared_state:
        stages_completed.append("✓ Context loaded")
    
    if "assessed_needs" in shared_state.get("document", {}):
        stages_completed.append("✓ Needs assessment completed")
    
    if "outline" in shared_state.get("document", {}):
        stages_completed.append("✓ Outline created")
    
    if "assignments" in shared_state:
        stages_completed.append("✓ Roles assigned")
    
    if shared_state.get("document", {}).get("status") == "drafted":
        stages_completed.append("✓ Document drafted")
    
    if "reviews" in shared_state:
        stages_completed.append("✓ Peer review conducted")
    
    if "version_control" in shared_state:
        stages_completed.append("✓ Version control applied")
    
    if shared_state.get("working_group_approved"):
        stages_completed.append("✓ Working group approved")
    
    if shared_state.get("committee_submitted"):
        stages_completed.append("✓ Committee submission completed")
    
    if shared_state.get("committee_approved"):
        stages_completed.append("✓ Committee approved")
    
    if shared_state.get("published"):
        stages_completed.append("✓ Document published")
    
    if shared_state.get("training_completed"):
        stages_completed.append("✓ Training completed")
    
    if shared_state.get("maintenance_active"):
        stages_completed.append("✓ Maintenance active")
    
    if shared_state.get("archived"):
        stages_completed.append("✓ Document archived")
    
    # Print results
    for stage in stages_completed:
        print(stage)
    
    print(f"\nTotal stages completed: {len(stages_completed)}")
    print(f"Final workflow result: {result}")
    
    # Check audit trail
    if "audit_trail" in shared_state:
        print(f"\nAudit trail entries: {len(shared_state['audit_trail'])}")
        print("\nLast 5 audit entries:")
        for entry in shared_state["audit_trail"][-5:]:
            print(f"  - {entry['node']}: {entry['action']}")
    
    return len(stages_completed) >= 10  # Expect at least 10 stages

if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1)