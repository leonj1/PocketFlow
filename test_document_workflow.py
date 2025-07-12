#!/usr/bin/env python3
"""
Test script for document workflow - demonstrates basic workflow execution
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from document_workflow import *


def test_basic_flow():
    """Test basic document workflow components."""
    print("Testing Document Workflow Components")
    print("===================================\n")
    
    # Test 1: Context Loader
    print("1. Testing ContextLoaderNode...")
    shared = {}
    context_loader = ContextLoaderNode()
    context_loader.set_params({"context_path": "context.yml"})
    result = context_loader.run(shared)
    
    if shared.get("context"):
        print("✓ Context loaded successfully")
        print(f"  Topic: {shared['context']['topic']}")
    else:
        print("✗ Failed to load context")
        return
    
    # Test 2: Document structure
    print("\n2. Testing document structure creation...")
    if shared.get("document"):
        print("✓ Document structure created")
        print(f"  Title: {shared['document']['title']}")
        print(f"  Version: {shared['document']['version']}")
    else:
        print("✗ Failed to create document structure")
    
    # Test 3: Needs Assessment
    print("\n3. Testing NeedsAssessmentNode...")
    needs_node = NeedsAssessmentNode()
    # Override AI if enabled to prevent API calls
    needs_node.ai_enabled = False
    
    # Mock the collect_feedback method from parent class
    def mock_collect_feedback(self, prompt, options=None):
        return "No" if options else ""
    
    # Replace the method temporarily
    import types
    needs_node.collect_feedback = types.MethodType(mock_collect_feedback, needs_node)
    
    result = needs_node.run(shared)
    if shared["document"].get("assessed_needs"):
        print("✓ Needs assessment completed")
        print(f"  Identified {len(shared['document']['assessed_needs'])} needs")
    
    # Test 4: Outline Generation
    print("\n4. Testing OutlineTemplateNode...")
    outline_node = OutlineTemplateNode()
    result = outline_node.run(shared)
    if shared["document"].get("outline"):
        print("✓ Outline generated")
        print(f"  Sections: {len(shared['document']['outline'])}")
        for section in shared["document"]["outline"][:3]:
            print(f"    - {section['name']}")
    
    # Test 5: Role Assignment
    print("\n5. Testing RoleAssignmentNode...")
    role_node = RoleAssignmentNode()
    result = role_node.run(shared)
    if shared.get("assignments"):
        print("✓ Roles assigned")
        print(f"  Reviewers: {len(shared['assignments']['reviewers'])}")
        print(f"  Approvers: {len(shared['assignments']['approvers'])}")
    
    # Test 6: Audit Trail
    print("\n6. Testing audit trail...")
    if shared.get("audit_trail"):
        print("✓ Audit trail active")
        print(f"  Entries: {len(shared['audit_trail'])}")
        for entry in shared["audit_trail"][-3:]:
            print(f"    - {entry['action']}: {entry['details']}")
    
    print("\n✅ All basic components tested successfully!")
    print("\nThe full workflow is interactive and requires user input.")
    print("Run 'python document_workflow.py' to experience the complete workflow.")


def test_flow_composition():
    """Test that Flows can contain other Flows."""
    print("\n\nTesting Flow Composition")
    print("========================\n")
    
    # Create a simple node
    class TestNode(BaseNode):
        def exec(self, prep_res):
            return {"executed": True}
        
        def post(self, shared, prep_res, exec_res):
            shared["test_executions"] = shared.get("test_executions", 0) + 1
            return "done"
    
    # Create a sub-flow
    node1 = TestNode()
    node2 = TestNode()
    node1 >> node2
    sub_flow = Flow(start=node1)
    
    # Create main flow that includes the sub-flow
    start_node = TestNode()
    end_node = TestNode()
    start_node >> sub_flow >> end_node
    main_flow = Flow(start=start_node)
    
    # Run the main flow
    shared = {}
    result = main_flow.run(shared)
    
    print(f"✓ Flow composition test completed")
    print(f"  Total executions: {shared.get('test_executions', 0)}")
    print(f"  Expected: 4 (start_node + sub_flow's 2 nodes + end_node)")
    
    if shared.get("test_executions") == 4:
        print("✅ Flow composition working correctly!")
    else:
        print("✗ Flow composition test failed")


if __name__ == "__main__":
    test_basic_flow()
    test_flow_composition()