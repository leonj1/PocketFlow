import yaml
from pocketflow import Node, Flow
from flows.section_based import (
    section_coordinator,
    parallel_section_node,
    section_review,
    document_assembler,
    SectionDraftingNode
)
from flows.section_committee import section_committee_node
from flows.completeness import (
    document_completeness_node,
    section_completeness_node,
    completeness_report_node
)
from flows.working_group import group_lead_node
import asyncio

class SectionBasedLeadNode(Node):
    """Modified lead node that works with section-based approach"""
    
    def prep(self, shared):
        print("\n Section-Based Lead Node")
        
        # Check if we've exceeded max attempts
        if shared["attempts"]["current"] >= shared["attempts"]["max"]:
            return "abandon"
            
        # Check if we have sections needing revision
        if "sections" in shared:
            sections_needing_work = [
                name for name, data in shared["sections"].items()
                if data["status"] in ["pending", "needs_revision"]
            ]
            
            if not sections_needing_work:
                print("All sections completed!")
                return "all_sections_complete"
        
        return "continue"
    
    def post(self, shared, prep_res, exec_res):
        if prep_res == "abandon":
            return "abandon"
        elif prep_res == "all_sections_complete":
            return "ready_for_assembly"
        return None

class SectionRevisionNode(Node):
    """Handles revision of sections based on feedback"""
    
    def prep(self, shared):
        print("\n Section Revision Node")
        
        if "sections" not in shared:
            return None
            
        # Find sections needing revision
        sections_to_revise = []
        for name, data in shared["sections"].items():
            if data["status"] == "needs_revision" and any(
                data["feedback"][key] for key in ["things_to_remove", "things_to_add", "things_to_change"]
            ):
                sections_to_revise.append(name)
        
        if not sections_to_revise:
            return None
            
        return {"sections_to_revise": sections_to_revise}
    
    async def exec_async(self, prep_data):
        if not prep_data:
            return None
            
        # Process revisions for each section
        for section_name in prep_data["sections_to_revise"]:
            print(f"Revising section: {section_name}")
            # Mark section as ready for re-processing
            # The actual revision will be handled by SectionDraftingNode
            # with the feedback incorporated
        
        return "revisions_queued"
    
    def post(self, shared, prep_res, exec_res):
        if exec_res == "revisions_queued":
            # Reset sections for re-processing
            for name, data in shared["sections"].items():
                if data["status"] == "needs_revision":
                    data["status"] = "pending"
                    data["review_status"] = None
        return None

class CompletenessGateNode(Node):
    """Checks if document meets completeness requirements before proceeding"""
    
    def prep(self, shared):
        print("\n Completeness Gate Check")
        
        if "completeness_analysis" not in shared:
            return None
            
        analysis = shared["completeness_analysis"]
        score = analysis["overall_completeness"]
        
        return {
            "score": score,
            "critical_issues": len(analysis.get("unfulfilled_goals", [])) + 
                              len(analysis.get("scope_violations", []))
        }
    
    def post(self, shared, prep_res, exec_res):
        if prep_res:
            score = prep_res["score"]
            critical_issues = prep_res["critical_issues"]
            
            if score < 70 or critical_issues > 0:
                print(f"  - Completeness insufficient: {score}/100 with {critical_issues} critical issues")
                # Increment attempts
                shared["attempts"]["current"] += 1
                return "needs_improvement"
            else:
                print(f"  - Completeness acceptable: {score}/100")
                return "completeness_ok"
        
        return "completeness_ok"  # Default to OK if no analysis

class EndNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nSection-based Document Generator completed successfully!")
        if "document" in shared:
            print(f"Final document word count: {len(shared['document'].split())}")
        if "sections" in shared:
            print("\nSection Summary:")
            for name, data in shared["sections"].items():
                print(f"  - {name}: {data['word_count']} words, "
                      f"Quality: {data.get('quality_score', 'N/A')}/10")
        if "completeness_analysis" in shared:
            print(f"\nDocument Completeness: {shared['completeness_analysis']['overall_completeness']}/100")
        pass

class AbandonNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nAbandoning document creation - max attempts reached")
        if "sections" in shared:
            completed = sum(1 for s in shared["sections"].values() if s["status"] == "completed")
            total = len(shared["sections"])
            print(f"Completed {completed}/{total} sections before abandoning")
        pass

class PublisherNode(Node):
    def prep(self, shared):
        print("\n Publisher Node")
        return {
            "document": shared["document"],
            "output_filename": shared["context"]["output_filename"]
        }
    
    def exec(self, prep_res):
        # Save the document
        with open(prep_res["output_filename"], "w") as f:
            f.write(prep_res["document"])
        
        # Also save section metadata
        metadata_filename = prep_res["output_filename"].replace(".md", "_metadata.yaml")
        if "sections" in shared:
            metadata = {
                "sections": {
                    name: {
                        "word_count": data["word_count"],
                        "quality_score": data.get("quality_score", "N/A"),
                        "version": data["version"],
                        "reviewer_scores": data.get("reviewer_scores", {})
                    }
                    for name, data in shared["sections"].items()
                },
                "completeness": shared.get("completeness_analysis", {}).get("overall_completeness", "N/A")
            }
            with open(metadata_filename, "w") as f:
                yaml.dump(metadata, f, default_flow_style=False)
        
        return None
    
    def post(self, shared, prep_res, exec_res):
        print(f"\n Publisher Node Completed. Document saved to: {prep_res['output_filename']}")
        return None

def main():
    print("\nWelcome to Section-Based Document Generator with Completeness Analysis!")
    print("=====================================================================")
    
    # Initialize shared store
    with open("/app/cookbook/doc-generator/context.yml", "r") as f:
        context = yaml.safe_load(f)
    
    shared = {
        "context": context,
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
    
    # Create nodes
    section_lead_node = SectionBasedLeadNode()
    section_revision_node = SectionRevisionNode()
    completeness_gate = CompletenessGateNode()
    abandon_node = AbandonNode()
    end_node = EndNode()
    publisher_node = PublisherNode()
    
    # Build the section-based workflow with completeness checks
    
    # Lead node checks status
    section_lead_node >> section_coordinator
    section_lead_node - "abandon" >> abandon_node
    section_lead_node - "ready_for_assembly" >> document_assembler
    
    # Section coordinator identifies ready sections
    section_coordinator >> parallel_section_node
    
    # Parallel processing of sections with inline completeness checks
    parallel_section_node >> section_completeness_node
    
    # Section completeness check
    section_completeness_node >> section_review
    
    # Section review
    section_review >> section_lead_node  # Loop back to check for more sections
    
    # Document assembly when all sections complete
    document_assembler >> document_completeness_node
    
    # Document-wide completeness analysis
    document_completeness_node >> completeness_report_node
    
    # Completeness gate check
    completeness_report_node >> completeness_gate
    
    # Gate outcomes
    completeness_gate - "completeness_ok" >> section_committee_node
    completeness_gate - "needs_improvement" >> section_revision_node
    
    # Committee review with section awareness
    section_committee_node - "approved_by_committee" >> publisher_node
    section_committee_node - "rejected_by_committee" >> section_revision_node
    
    # Revision handling
    section_revision_node >> section_lead_node  # Loop back to reprocess
    
    # Final nodes
    publisher_node >> end_node
    
    # Create and run the flow
    section_flow = Flow(start=section_lead_node)
    
    print("\nStarting section-based document generation with completeness analysis...")
    print("This will:")
    print("  1. Process document sections individually")
    print("  2. Check readability against target audience")
    print("  3. Analyze conceptual coherence")
    print("  4. Verify goal fulfillment")
    print("  5. Ensure scope compliance")
    print("\n")
    
    try:
        section_flow.run(shared)
    except Exception as e:
        print(f"\nError during document generation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nSection-Based Document Generator with Completeness Analysis finished!")

if __name__ == "__main__":
    # Ensure output directory exists
    import os
    os.makedirs("output", exist_ok=True)
    
    main()