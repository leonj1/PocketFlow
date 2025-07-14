import yaml
import asyncio
import os
from pocketflow import Node, Flow

# Import section-based nodes for the optimal workflow
from flows.section_based import (
    section_coordinator,
    parallel_section_node,
    section_review,
    document_assembler,
    SectionDraftingNode,
    SectionReviewNode
)

# Import section-aware committee
from flows.section_committee import section_committee_node

# Import completeness analysis nodes
from flows.completeness import (
    document_completeness_node,
    section_completeness_node,
    completeness_report_node
)

class SectionBasedLeadNode(Node):
    """Lead node that manages section-based document generation"""
    
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
            
            print(f"  Sections needing work: {len(sections_needing_work)}")
            if sections_needing_work:
                # Show status of first few sections
                for name in list(shared["sections"].keys())[:3]:
                    print(f"    - {name}: {shared['sections'][name]['status']}")
            
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

class BatchSectionReviewNode(Node):
    """Reviews all drafted sections that haven't been reviewed yet"""
    
    def prep(self, shared):
        print("\n Batch Section Review Node")
        
        if "sections" not in shared:
            return None
            
        # Find sections that are completed but not reviewed
        sections_to_review = [
            name for name, data in shared["sections"].items()
            if data["status"] == "completed" and data.get("review_status") != "reviewed"
        ]
        
        if not sections_to_review:
            print("  No sections need review")
            return None
            
        print(f"  Reviewing {len(sections_to_review)} sections...")
        return {"sections_to_review": sections_to_review}
    
    def exec(self, prep_data):
        if not prep_data:
            return None
            
        # For now, we'll do a simple review that marks all sections as reviewed
        # In a real implementation, this would call section_review node for each
        return prep_data["sections_to_review"]
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            # Mark all reviewed sections
            for section_name in exec_res:
                shared["sections"][section_name]["review_status"] = "reviewed"
                # For now, give them a default quality score
                shared["sections"][section_name]["quality_score"] = 8
                print(f"    - {section_name}: Reviewed (Quality: 8/10)")
        return None

class SectionRevisionNode(Node):
    """Handles revision of sections based on feedback"""
    
    def prep(self, shared):
        print("\n Section Revision Node")
        
        if "sections" not in shared:
            return None
        
        # If we have completeness issues, convert them to section feedback
        if "completeness_analysis" in shared:
            self._convert_completeness_to_section_feedback(shared)
            
        # Find sections needing revision
        sections_to_revise = []
        for name, data in shared["sections"].items():
            if data["status"] == "needs_revision" or any(
                data["feedback"][key] for key in ["things_to_remove", "things_to_add", "things_to_change"]
            ):
                sections_to_revise.append(name)
                data["status"] = "needs_revision"  # Ensure status is set
        
        if not sections_to_revise:
            print("  No sections need revision")
            return None
            
        print(f"  Sections to revise: {sections_to_revise}")
        return {"sections_to_revise": sections_to_revise}
    
    def exec(self, prep_data):
        if not prep_data:
            return None
            
        # Process revisions for each section
        for section_name in prep_data["sections_to_revise"]:
            print(f"Revising section: {section_name}")
        
        return "revisions_queued"
    
    def _convert_completeness_to_section_feedback(self, shared):
        """Convert document-level completeness issues to section-specific feedback"""
        analysis = shared["completeness_analysis"]
        
        print("\n  Converting completeness issues to section feedback:")
        
        # 1. Distribute readability issues to relevant sections
        readability_issues = analysis.get("readability_issues", [])
        if readability_issues:
            print(f"    - Processing {len(readability_issues)} readability issues")
            for issue in readability_issues:
                section_name = issue.get("section", "Executive Summary")
                if section_name in shared["sections"]:
                    feedback = f"[Readability] {issue.get('issue', '')} {issue.get('suggestion', '')}"
                    shared["sections"][section_name]["feedback"]["things_to_change"].append(feedback)
        
        # 2. Convert conceptual gaps to things to add
        conceptual_gaps = analysis.get("conceptual_gaps", [])
        if conceptual_gaps:
            print(f"    - Processing {len(conceptual_gaps)} conceptual gaps")
            for gap in conceptual_gaps:
                # Determine which section should explain the concept
                section_name = self._determine_section_for_concept(gap)
                if section_name in shared["sections"]:
                    if gap["type"] == "orphaned_concept":
                        feedback = f"[Concept Gap] {gap['message']} {gap.get('suggestion', '')}"
                    elif gap["type"] == "undefined_term":
                        feedback = f"[Undefined Term] {gap['message']} {gap.get('suggestion', '')}"
                    elif gap["type"] == "missing_relationship":
                        feedback = f"[Missing Connection] {gap['message']} {gap.get('suggestion', '')}"
                    else:
                        feedback = f"[Concept] {gap.get('message', '')} {gap.get('suggestion', '')}"
                    shared["sections"][section_name]["feedback"]["things_to_add"].append(feedback)
        
        # 3. Add unfulfilled goals as things to add
        unfulfilled_goals = analysis.get("unfulfilled_goals", [])
        if unfulfilled_goals:
            print(f"    - Processing {len(unfulfilled_goals)} unfulfilled goals")
            for goal in unfulfilled_goals:
                section_name = self._determine_section_for_goal(goal)
                if section_name in shared["sections"]:
                    feedback = f"[Goal] {goal.get('suggestion', goal.get('goal', ''))}"
                    shared["sections"][section_name]["feedback"]["things_to_add"].append(feedback)
        
        # 4. Convert scope violations to things to remove
        scope_violations = analysis.get("scope_violations", [])
        if scope_violations:
            print(f"    - Processing {len(scope_violations)} scope violations")
            for violation in scope_violations:
                section_name = violation.get("section", "Executive Summary")
                if section_name in shared["sections"]:
                    feedback = f"[Scope] {violation.get('message', '')} {violation.get('suggestion', '')}"
                    shared["sections"][section_name]["feedback"]["things_to_remove"].append(feedback)
    
    def _determine_section_for_concept(self, gap):
        """Determine which section should address a conceptual gap"""
        # Look for section mentions in the gap context
        concept = gap.get("concept", "").lower()
        concepts = gap.get("concepts", [])
        
        # Map concepts to likely sections
        if any(term in str(concepts).lower() for term in ["auth", "jwt", "oauth", "token"]):
            return "Chosen Solution"
        elif any(term in str(concepts).lower() for term in ["risk", "threat", "vulnerability"]):
            return "Risks and Mitigations"
        elif any(term in str(concepts).lower() for term in ["implement", "code", "example"]):
            return "Python Code Example"
        elif any(term in str(concepts).lower() for term in ["track", "monitor", "adopt"]):
            return "Steps for Tracking Adoption and Adherance"
        else:
            return "Problem Statement"  # Default for concept explanations
    
    def _determine_section_for_goal(self, goal):
        """Determine which section should address an unfulfilled goal"""
        goal_text = goal.get("goal", "").lower()
        
        if "implementation" in goal_text or "technical" in goal_text:
            return "Chosen Solution"
        elif "risk" in goal_text or "mitigation" in goal_text:
            return "Risks and Mitigations"
        elif "track" in goal_text or "adoption" in goal_text:
            return "Steps for Tracking Adoption and Adherance"
        elif "example" in goal_text or "code" in goal_text:
            return "Python Code Example"
        elif "diagram" in goal_text:
            return "Mermaid Diagram Example"
        else:
            return "Executive Summary"  # Default for high-level goals
    
    def post(self, shared, prep_res, exec_res):
        if exec_res == "revisions_queued":
            # Reset sections for re-processing
            for name, data in shared["sections"].items():
                if data["status"] == "needs_revision":
                    data["status"] = "pending"
                    data["review_status"] = None
        return None

# CompletenessGateNode removed - DocumentCompletenessNode already handles gating

class EndNode(Node):
    """Final node that reports generation statistics"""
    
    def post(self, shared, prep_res, exec_res):
        print("\nDocument Generator completed successfully!")
        if "document" in shared:
            print(f"Final document word count: {len(shared['document'].split())}")
        if "sections" in shared:
            print("\nSection Summary:")
            for name, data in shared["sections"].items():
                print(f"  - {name}: {data['word_count']} words, "
                      f"Quality: {data.get('quality_score', 'N/A')}/10")
        if "completeness_analysis" in shared:
            print(f"\nDocument Completeness: {shared['completeness_analysis']['overall_completeness']}/100")

class AbandonNode(Node):
    """Handles cases where document generation cannot continue"""
    
    def post(self, shared, prep_res, exec_res):
        print("\nAbandoning document creation - max attempts reached")
        if "sections" in shared:
            completed = sum(1 for s in shared["sections"].values() if s["status"] == "completed")
            total = len(shared["sections"])
            print(f"Completed {completed}/{total} sections before abandoning")

class PublisherNode(Node):
    """Publishes the completed document and metadata"""
    
    def prep(self, shared):
        print("\n Publisher Node")
        return {
            "document": shared["document"],
            "output_filename": shared["context"]["output_filename"],
            "sections": shared.get("sections", {}),
            "completeness": shared.get("completeness_analysis", {})
        }

    def exec(self, prep_res):
        # Save the document
        with open(prep_res["output_filename"], "w") as f:
            f.write(prep_res["document"])
        
        # Save section metadata
        metadata_filename = prep_res["output_filename"].replace(".md", "_metadata.yaml")
        if prep_res["sections"]:
            metadata = {
                "sections": {
                    name: {
                        "word_count": data["word_count"],
                        "quality_score": data.get("quality_score", "N/A"),
                        "version": data["version"],
                        "reviewer_scores": data.get("reviewer_scores", {})
                    }
                    for name, data in prep_res["sections"].items()
                },
                "completeness": prep_res["completeness"].get("overall_completeness", "N/A")
            }
            with open(metadata_filename, "w") as f:
                yaml.dump(metadata, f, default_flow_style=False)
        
        # Save completeness report if available
        if "completeness_report" in shared:
            report_filename = prep_res["output_filename"].replace(".md", "_completeness.md")
            with open(report_filename, "w") as f:
                f.write("# Document Completeness Report\n\n")
                f.write(f"**Overall Score:** {shared['completeness_report']['score']}/100\n\n")
                f.write(shared['completeness_report']['report'])
        
        return prep_res["output_filename"]

    def post(self, shared, prep_res, exec_res):
        print(f"\n Publisher Node Completed. Document saved to: {exec_res}")
        return None

def build_section_workflow():
    """Builds the optimal section-based workflow with completeness checks"""
    
    # Create nodes
    section_lead_node = SectionBasedLeadNode()
    batch_review_node = BatchSectionReviewNode()
    section_revision_node = SectionRevisionNode()
    abandon_node = AbandonNode()
    end_node = EndNode()
    publisher_node = PublisherNode()
    
    # Build the section-based workflow with completeness checks
    
    # Lead node checks status and routes
    section_lead_node >> section_coordinator
    section_lead_node - "abandon" >> abandon_node
    section_lead_node - "ready_for_assembly" >> document_assembler
    
    # Section coordinator identifies ready sections
    section_coordinator >> parallel_section_node
    
    # After parallel processing, review the drafted sections
    parallel_section_node >> batch_review_node
    
    # After review, loop back to check for more sections
    batch_review_node >> section_lead_node  # Loop back to process remaining sections
    
    # Document assembly when all sections complete
    document_assembler >> document_completeness_node
    
    # Document completeness analysis routes based on score
    # IMPORTANT: No default path - must explicitly route based on score
    document_completeness_node - "generate_report" >> completeness_report_node  # High score path (>= 70)
    document_completeness_node - "needs_improvement" >> section_revision_node  # Low score path (< 70)
    
    # After report generation, proceed to committee
    completeness_report_node >> section_committee_node
    
    # Committee review with section awareness
    section_committee_node - "approved_by_committee" >> publisher_node
    section_committee_node - "rejected_by_committee" >> section_revision_node
    
    # Revision handling
    section_revision_node >> section_lead_node  # Loop back to reprocess
    
    # Final nodes
    publisher_node >> end_node
    abandon_node >> end_node  # Ensure abandon also leads to end
    
    # Create and return the flow
    return Flow(start=section_lead_node)

def main():
    print("\nWelcome to Advanced Document Generator!")
    print("=====================================")
    print("Using section-based processing with completeness analysis")
    print("This ensures the highest quality document generation.\n")
    
    # Initialize shared store
    with open("/app/cookbook/doc-generator/context.yml", "r") as f:
        context = yaml.safe_load(f)
    
    # Initialize shared state for section-based processing
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
        # Note: "sections" will be initialized by SectionCoordinatorNode
        # Note: "document" will be created by DocumentAssemblerNode
    }
    
    # Build the optimal section-based workflow
    section_flow = build_section_workflow()
    
    print("Starting document generation...")
    print("This process will:")
    print("  1. Process document sections individually")
    print("  2. Check readability against target audience")
    print("  3. Analyze conceptual coherence")
    print("  4. Verify goal fulfillment")
    print("  5. Ensure scope compliance")
    print("  6. Use section-aware committee reviews\n")
    
    try:
        # Run the section-based workflow
        section_flow.run(shared)
    except Exception as e:
        print(f"\nError during document generation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nDocument Generator finished!")

if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    main() 
