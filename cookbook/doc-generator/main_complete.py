import yaml
from pocketflow import Node, Flow
from flows.working_group_complete import enhanced_working_group_flow, enhanced_group_evaluator_node, enhanced_group_lead_node, completeness_gate
from flows.committee_complete import enhanced_committee_node
from flows.completeness import completeness_report_node

class EndNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nEnhanced Document Generator completed!")
        
        # Display final statistics
        if "document" in shared:
            print(f"  - Document length: {len(shared['document'].split())} words")
        
        if "completeness_analysis" in shared:
            analysis = shared["completeness_analysis"]
            print(f"  - Final completeness score: {analysis['overall_completeness']}/100")
            print(f"  - Readability issues: {len(analysis.get('readability_issues', []))}")
            print(f"  - Conceptual gaps: {len(analysis.get('conceptual_gaps', []))}")
            print(f"  - Unfulfilled goals: {len(analysis.get('unfulfilled_goals', []))}")
            print(f"  - Scope violations: {len(analysis.get('scope_violations', []))}")
        
        if "approvals" in shared:
            print(f"  - Committee votes: {shared['approvals']['in_favor']} in favor, "
                  f"{shared['approvals']['against']} against, "
                  f"{shared['approvals']['abstain']} abstained")
        pass

class AbandonNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nAbandoning document creation - max attempts reached")
        
        if "completeness_analysis" in shared:
            analysis = shared["completeness_analysis"]
            print(f"  - Best completeness achieved: {analysis['overall_completeness']}/100")
            
            # Show what prevented completion
            issues = []
            if analysis.get("unfulfilled_goals"):
                issues.append(f"{len(analysis['unfulfilled_goals'])} unfulfilled goals")
            if analysis.get("scope_violations"):
                issues.append(f"{len(analysis['scope_violations'])} scope violations")
            if analysis.get("readability_issues"):
                issues.append(f"{len(analysis['readability_issues'])} readability issues")
            
            if issues:
                print(f"  - Blocking issues: {', '.join(issues)}")
        pass

class PublisherNode(Node):
    def prep(self, shared):
        print("\n Publisher Node")
        return {
            "document": shared["document"],
            "output_filename": shared["context"]["output_filename"],
            "completeness_report": shared.get("completeness_report", None)
        }
    
    def exec(self, prep_res):
        # Save the document
        with open(prep_res["output_filename"], "w") as f:
            f.write(prep_res["document"])
        
        # Save completeness report if available
        if prep_res["completeness_report"]:
            report_filename = prep_res["output_filename"].replace(".md", "_completeness.md")
            with open(report_filename, "w") as f:
                f.write("# Document Completeness Report\n\n")
                f.write(f"**Overall Score:** {prep_res['completeness_report']['score']}/100\n\n")
                f.write(prep_res['completeness_report']['report'])
        
        # Save metadata
        metadata_filename = prep_res["output_filename"].replace(".md", "_metadata.yaml")
        metadata = {
            "completeness_score": shared.get("completeness_analysis", {}).get("overall_completeness", "N/A"),
            "committee_approval": {
                "in_favor": shared.get("approvals", {}).get("in_favor", 0),
                "against": shared.get("approvals", {}).get("against", 0),
                "abstain": shared.get("approvals", {}).get("abstain", 0)
            },
            "revision_attempts": shared.get("attempts", {}).get("current", 0)
        }
        
        with open(metadata_filename, "w") as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        return None
    
    def post(self, shared, prep_res, exec_res):
        print(f"\n Publisher Node Completed")
        print(f"  - Document saved to: {prep_res['output_filename']}")
        
        if prep_res["completeness_report"]:
            report_filename = prep_res["output_filename"].replace(".md", "_completeness.md")
            print(f"  - Completeness report saved to: {report_filename}")
        return None

def main():
    print("\nWelcome to Enhanced Document Generator with Completeness Analysis!")
    print("================================================================")
    print("\nThis enhanced version includes:")
    print("  - Readability analysis for target audience")
    print("  - Conceptual coherence checking")
    print("  - Goal fulfillment tracking")
    print("  - Scope compliance validation")
    print("  - Quality gates before committee review\n")
    
    # Initialize shared store
    with open("/app/cookbook/doc-generator/context.yml", "r") as f:
        context = yaml.safe_load(f)
    
    shared = {
        "context": context,
        "next_step": "start",
        "document": {
            "title": "",
            "sections": []
        },
        "attempts": {
            "current": 0,
            "max": 3
        },
        "feedback": {
            "things_to_remove": [],
            "things_to_add": [],
            "things_to_change": []
        },
        "approvals": {
            "in_favor": 0,
            "against": 0,
            "abstain": 0
        }
    }
    
    # Create flow nodes
    abandon_node = AbandonNode()
    end_node = EndNode()
    publisher_node = PublisherNode()
    
    # Connect enhanced nodes
    # Working group flow already connected internally
    # Connect completeness gate outcomes
    completeness_gate - "ready_for_committee" >> enhanced_committee_node
    
    # Connect lead node abandon path
    enhanced_group_lead_node - "abandon" >> abandon_node
    
    # Committee outcomes
    enhanced_committee_node - "approved_by_committee" >> publisher_node
    enhanced_committee_node - "rejected_by_committee" >> enhanced_group_lead_node
    
    # Final node
    publisher_node >> end_node
    
    # Run the enhanced flow
    print("Starting enhanced document generation with completeness checks...\n")
    
    try:
        enhanced_working_group_flow.run(shared)
    except Exception as e:
        print(f"\nError during enhanced document generation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nEnhanced Document Generator finished!")

if __name__ == "__main__":
    # Ensure output directory exists
    import os
    os.makedirs("output", exist_ok=True)
    
    main()