#!/usr/bin/env python3
"""
Comprehensive test suite for PocketFlow Document Workflow
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from document_workflow import (
    DocumentNode, ReviewNode, ApprovalNode, ContextLoaderNode,
    NeedsAssessmentNode, OutlineTemplateNode, RoleAssignmentNode,
    DocumentDraftingNode, PeerReviewNode, VersionControlNode,
    WorkingGroupFlow, CommitteeFlow, DocumentWorkflow
)
from pocketflow import Node, Flow, BaseNode


class TestDocumentNode:
    """Test the base DocumentNode class."""
    
    def test_document_node_initialization(self):
        """Test DocumentNode can be initialized."""
        node = DocumentNode()
        assert isinstance(node, DocumentNode)
        assert isinstance(node, Node)
    
    def test_get_context(self):
        """Test getting context from shared state."""
        node = DocumentNode()
        shared = {"context": {"topic": "Test Topic"}}
        context = node.get_context(shared)
        assert context["topic"] == "Test Topic"
    
    def test_get_document(self):
        """Test getting document from shared state."""
        node = DocumentNode()
        shared = {"document": {"title": "Test Document"}}
        document = node.get_document(shared)
        assert document["title"] == "Test Document"
    
    def test_update_document(self):
        """Test updating document in shared state."""
        node = DocumentNode()
        shared = {"document": {"title": "Old Title"}}
        node.update_document(shared, {"title": "New Title", "version": "1.0"})
        assert shared["document"]["title"] == "New Title"
        assert shared["document"]["version"] == "1.0"
    
    def test_add_audit_entry(self):
        """Test adding audit trail entries."""
        node = DocumentNode()
        shared = {}
        node.add_audit_entry(shared, "test_action", "Test details")
        
        assert "audit_trail" in shared
        assert len(shared["audit_trail"]) == 1
        assert shared["audit_trail"][0]["action"] == "test_action"
        assert shared["audit_trail"][0]["details"] == "Test details"


class TestContextLoaderNode:
    """Test the ContextLoaderNode."""
    
    def test_context_loader_with_valid_file(self, tmp_path):
        """Test loading valid context YAML."""
        # Create test context file
        context_data = {
            "topic": "Test Document",
            "purpose": "Testing",
            "audience": {"primary": [{"role": "Testers"}]},
            "scope": {"includes": ["Testing"]},
            "deliverables": [{"type": "Main Document"}]
        }
        
        context_file = tmp_path / "test_context.yml"
        with open(context_file, 'w') as f:
            yaml.dump(context_data, f)
        
        # Test loading
        node = ContextLoaderNode()
        node.set_params({"context_path": str(context_file)})
        
        shared = {}
        result = node.run(shared)
        
        assert result == None  # Fixed: should return None to continue
        assert "context" in shared
        assert shared["context"]["topic"] == "Test Document"
        assert "document" in shared
        assert shared["document"]["title"] == "Test Document"
    
    def test_context_loader_missing_required_fields(self, tmp_path):
        """Test loading context with missing required fields."""
        # Create incomplete context file
        context_data = {"topic": "Test Document"}  # Missing required fields
        
        context_file = tmp_path / "incomplete_context.yml"
        with open(context_file, 'w') as f:
            yaml.dump(context_data, f)
        
        node = ContextLoaderNode()
        node.set_params({"context_path": str(context_file)})
        
        shared = {}
        result = node.run(shared)
        
        assert result == "error"


class TestWorkflowNodes:
    """Test various workflow nodes."""
    
    def test_needs_assessment_node(self):
        """Test NeedsAssessmentNode."""
        node = NeedsAssessmentNode()
        # Disable AI to avoid API calls
        node.ai_enabled = False
        
        shared = {
            "context": {
                "topic": "Test Topic",
                "audience": {"primary": [{"role": "Developers"}]},
                "scope": {"includes": ["Feature A", "Feature B"]},
                "constraints": {"timeline": "2 weeks"}
            },
            "document": {}
        }
        
        # Mock user input - now collect_feedback exists since we inherit from ReviewNode
        with patch.object(node, 'collect_feedback', return_value="No"):
            result = node.run(shared)
        
        assert result == None  # Fixed: should return None to continue
        assert "assessed_needs" in shared["document"]
        assert len(shared["document"]["assessed_needs"]) > 0
    
    def test_outline_template_node(self):
        """Test OutlineTemplateNode."""
        node = OutlineTemplateNode()
        shared = {
            "context": {
                "deliverables": [{
                    "type": "Main Document",
                    "sections": [
                        {"name": "Introduction", "max_pages": 2},
                        {"name": "Content", "max_pages": 10}
                    ]
                }]
            },
            "document": {"assessed_needs": ["Need 1", "Need 2"]}
        }
        
        result = node.run(shared)
        
        assert result == None  # Fixed: should return None to continue
        assert "outline" in shared["document"]
        assert len(shared["document"]["outline"]) == 2
        assert shared["document"]["outline"][0]["name"] == "Introduction"
    
    def test_role_assignment_node(self):
        """Test RoleAssignmentNode."""
        node = RoleAssignmentNode()
        shared = {
            "context": {
                "stakeholders": {
                    "reviewers": [{"group": "Team A"}, {"group": "Team B"}],
                    "approvers": [{"name": "Manager"}]
                }
            }
        }
        
        result = node.run(shared)
        
        assert result == None  # Fixed: should return None to continue
        assert "assignments" in shared
        assert len(shared["assignments"]["reviewers"]) == 2
        assert len(shared["assignments"]["approvers"]) == 1


class TestDocumentDraftingNode:
    """Test the DocumentDraftingNode."""
    
    def test_drafting_node_without_ai(self):
        """Test drafting with AI disabled."""
        node = DocumentDraftingNode()
        node.ai_enabled = False  # Ensure AI is disabled
        
        shared = {
            "context": {"topic": "Test Topic", "purpose": "Testing"},
            "document": {
                "title": "Test Document",
                "outline": [
                    {
                        "name": "Executive Summary",
                        "status": "pending",
                        "max_pages": 2,
                        "audience_focus": ["All"]
                    }
                ]
            }
        }
        
        result = node.run(shared)
        
        assert result == None  # Fixed: DocumentDraftingNode now returns None to continue
        assert shared["document"]["outline"][0]["status"] == "drafted"
        assert shared["document"]["outline"][0]["content"] != ""
        assert shared["document"]["outline"][0]["ai_generated"] == False


class TestReviewNodes:
    """Test review and approval nodes."""
    
    def test_peer_review_node(self):
        """Test PeerReviewNode."""
        node = PeerReviewNode()
        node.ai_enabled = False  # Disable AI for testing
        
        shared = {
            "context": {"topic": "Test Topic"},
            "document": {
                "title": "Test Document",
                "version": "0.1",
                "status": "drafted",
                "outline": [{
                    "name": "Section 1",
                    "status": "drafted",
                    "content": "Test content"
                }]
            }
        }
        
        # Mock user feedback
        feedback = {
            "overall": "Approve",
            "comments": "Good work",
            "specific_issues": []
        }
        
        with patch.object(node, 'collect_detailed_feedback', return_value=feedback):
            result = node.run(shared)
        
        assert result == "approved"
        assert "reviews" in shared
        assert len(shared["reviews"]) == 1
        assert shared["reviews"][0]["feedback"]["overall"] == "Approve"


class TestFlows:
    """Test the Flow compositions."""
    
    def test_working_group_flow_initialization(self):
        """Test WorkingGroupFlow can be initialized."""
        flow = WorkingGroupFlow()
        assert isinstance(flow, Flow)
        assert isinstance(flow, BaseNode)
        assert flow.start_node is not None
    
    def test_committee_flow_initialization(self):
        """Test CommitteeFlow can be initialized."""
        flow = CommitteeFlow()
        assert isinstance(flow, Flow)
        assert flow.start_node is not None
    
    def test_document_workflow_initialization(self):
        """Test main DocumentWorkflow can be initialized."""
        workflow = DocumentWorkflow()
        assert isinstance(workflow, Flow)
        assert workflow.start_node is not None


class TestFlowComposition:
    """Test that Flows can be used as Nodes."""
    
    def test_flow_is_node(self):
        """Test that Flow inherits from BaseNode."""
        flow = Flow()
        assert isinstance(flow, BaseNode)
    
    def test_nested_flows(self):
        """Test nesting flows within flows."""
        # Create simple nodes
        class SimpleNode(BaseNode):
            def exec(self, prep_res):
                return {"executed": True}
            
            def post(self, shared, prep_res, exec_res):
                shared["executions"] = shared.get("executions", 0) + 1
                # Return None or "default" to continue to next node
                return None
        
        # Create a sub-flow
        node1 = SimpleNode()
        node2 = SimpleNode()
        node1 >> node2
        sub_flow = Flow(start=node1)
        
        # Create main flow with sub-flow as a node
        start_node = SimpleNode()
        end_node = SimpleNode()
        start_node >> sub_flow >> end_node
        main_flow = Flow(start=start_node)
        
        # Run the flow
        shared = {}
        result = main_flow.run(shared)
        
        # Should execute all 4 nodes
        assert shared.get("executions") == 4


class TestAIIntegration:
    """Test AI integration components."""
    
    def test_ai_agent_disabled_mode(self):
        """Test AI agent when disabled."""
        from ai_agent import AiAgent
        
        # Create agent with AI disabled
        with patch.dict(os.environ, {"DOC_GENERATION_MODE": "human_only"}):
            agent = AiAgent()
            assert not agent.is_enabled()
            
            result = agent.invoke("Test query")
            assert "disabled" in result.lower()
    
    def test_document_ai_agent_fallbacks(self):
        """Test DocumentAiAgent fallback behavior."""
        from document_ai_agents import DocumentAiAgent
        
        # Create agent with AI disabled
        with patch.dict(os.environ, {"DOC_GENERATION_MODE": "human_only"}):
            agent = DocumentAiAgent()
            
            # Test section generation fallback
            section = agent.generate_section(
                section_name="Test Section",
                context={"topic": "Test"},
                max_pages=5
            )
            
            assert section.title == "Test Section"
            assert "Placeholder" in section.content
            assert section.estimated_pages == 1.0


def test_imports():
    """Test that all modules can be imported."""
    try:
        from document_workflow import DocumentWorkflow
        from ai_agent import AiAgent
        from document_ai_agents import DocumentAiAgent
        from pocketflow import Node, Flow
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])