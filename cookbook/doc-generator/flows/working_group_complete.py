from pocketflow import Node, Flow
import sys
sys.path.append('/app/cookbook/doc-generator')
from utils import call_llm, call_llm_thinking
from completeness import document_completeness_node, completeness_report_node
import yaml

# Import original nodes from working_group
from working_group import (
    GroupLeadNode,
    DocumentDraftingNode,
    ThingsToRemoveNode,
    ThingsToAddNode,
    ThingsToChangeNode,
    GroupEvaluatorNode
)

class EnhancedGroupLeadNode(GroupLeadNode):
    """Enhanced lead node that considers completeness feedback"""
    
    def prep(self, shared):
        print("\n Enhanced Group Lead Node")
        
        # Check if we've exceeded max attempts
        if shared["attempts"]["current"] >= shared["attempts"]["max"]:
            return "abandon"
        
        # Check if we have completeness feedback to address
        if "completeness_analysis" in shared:
            analysis = shared["completeness_analysis"]
            if analysis["overall_completeness"] < 70:
                print(f"  - Completeness score too low: {analysis['overall_completeness']}/100")
                # Convert completeness issues to feedback
                self._convert_completeness_to_feedback(shared, analysis)
        
        return shared["context"]
    
    def _convert_completeness_to_feedback(self, shared, analysis):
        """Convert completeness issues into actionable feedback"""
        
        # Add readability issues to things to change
        for issue in analysis.get("readability_issues", []):
            feedback_item = f"[Readability] {issue['issue']} {issue.get('suggestion', '')}"
            if feedback_item not in shared["feedback"]["things_to_change"]:
                shared["feedback"]["things_to_change"].append(feedback_item)
        
        # Add unfulfilled goals to things to add
        for goal in analysis.get("unfulfilled_goals", []):
            feedback_item = f"[Goal] {goal['suggestion']}"
            if feedback_item not in shared["feedback"]["things_to_add"]:
                shared["feedback"]["things_to_add"].append(feedback_item)
        
        # Add scope violations to things to remove
        for violation in analysis.get("scope_violations", []):
            feedback_item = f"[Scope] {violation['message']} {violation.get('suggestion', '')}"
            if feedback_item not in shared["feedback"]["things_to_remove"]:
                shared["feedback"]["things_to_remove"].append(feedback_item)
        
        # Add conceptual gaps to things to add
        for gap in analysis.get("conceptual_gaps", []):
            feedback_item = f"[Concepts] {gap['message']} {gap.get('suggestion', '')}"
            if feedback_item not in shared["feedback"]["things_to_add"]:
                shared["feedback"]["things_to_add"].append(feedback_item)

class EnhancedGroupEvaluatorNode(GroupEvaluatorNode):
    """Enhanced evaluator that triggers completeness analysis"""
    
    def post(self, shared, prep_res, exec_res):
        # Original post processing
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n Enhanced Group Evaluator Node Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print("\n Enhanced Group Evaluator Node Skipped - No context provided")
        
        # Trigger completeness analysis before committee
        return 'ready_for_completeness'

class CompletenessGateNode(Node):
    """Decides whether document is complete enough for committee review"""
    
    def prep(self, shared):
        print("\n Completeness Gate Check")
        
        if "completeness_analysis" not in shared:
            # No analysis performed, allow to proceed
            return {"decision": "proceed"}
        
        analysis = shared["completeness_analysis"]
        score = analysis["overall_completeness"]
        
        # Count critical issues
        critical_issues = (
            len(analysis.get("unfulfilled_goals", [])) +
            len(analysis.get("scope_violations", []))
        )
        
        return {
            "score": score,
            "critical_issues": critical_issues,
            "attempts": shared["attempts"]["current"]
        }
    
    def post(self, shared, prep_res, exec_res):
        if not prep_res:
            return "ready_for_committee"
        
        score = prep_res["score"]
        critical_issues = prep_res["critical_issues"]
        attempts = prep_res["attempts"]
        
        # Decision logic
        if score >= 85 and critical_issues == 0:
            print(f"  - Excellent completeness: {score}/100")
            return "ready_for_committee"
        elif score >= 70 and critical_issues <= 2:
            print(f"  - Acceptable completeness: {score}/100 with {critical_issues} issues")
            return "ready_for_committee"
        elif attempts >= shared["attempts"]["max"] - 1:
            print(f"  - Forcing committee review due to attempt limit")
            return "ready_for_committee"
        else:
            print(f"  - Insufficient completeness: {score}/100 with {critical_issues} critical issues")
            print(f"  - Returning for revision (attempt {attempts + 1}/{shared['attempts']['max']})")
            shared["attempts"]["current"] += 1
            return "needs_revision"

# Create enhanced nodes
enhanced_group_lead_node = EnhancedGroupLeadNode()
enhanced_group_evaluator_node = EnhancedGroupEvaluatorNode()
completeness_gate = CompletenessGateNode()

# Reuse original feedback nodes
things_to_remove_node = ThingsToRemoveNode()
things_to_add_node = ThingsToAddNode()
things_to_change_node = ThingsToChangeNode()
document_drafting_node = DocumentDraftingNode()

# Build enhanced flow with completeness checks
enhanced_group_lead_node >> things_to_remove_node
enhanced_group_lead_node - "abandon" >> None
things_to_remove_node >> things_to_add_node
things_to_add_node >> things_to_change_node
things_to_change_node >> document_drafting_node
document_drafting_node >> enhanced_group_evaluator_node

# Add completeness analysis branch
enhanced_group_evaluator_node - "ready_for_completeness" >> document_completeness_node
document_completeness_node >> completeness_report_node
completeness_report_node >> completeness_gate

# Gate decision routing
completeness_gate - "ready_for_committee" >> None  # Exit to committee
completeness_gate - "needs_revision" >> enhanced_group_lead_node  # Loop back

# Create the enhanced working group flow
enhanced_working_group_flow = Flow(start=enhanced_group_lead_node)