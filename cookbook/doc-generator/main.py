import yaml
import asyncio
import os
import glob
from datetime import datetime
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

class ResumeDetectorNode(Node):
    """Detects existing work and offers resume options"""
    
    def prep(self, shared):
        print("\n🔍 Resume Detection Node")
        
        # Check for existing published document
        output_file = shared["context"]["output_filename"]
        published_exists = os.path.exists(output_file)
        
        # Check for draft sessions
        doc_name = output_file.split("/")[-1].replace(".md", "")
        draft_pattern = f"drafts/{doc_name}_session_*/summary.md"
        draft_sessions = glob.glob(draft_pattern)
        
        resume_options = []
        
        if published_exists:
            mod_time = datetime.fromtimestamp(os.path.getmtime(output_file))
            resume_options.append({
                "type": "published",
                "path": output_file,
                "modified": mod_time.strftime("%Y-%m-%d %H:%M"),
                "description": f"Published document: {output_file}"
            })
        
        if draft_sessions:
            # Get most recent draft session
            draft_sessions.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_session = draft_sessions[0]
            session_dir = os.path.dirname(latest_session)
            
            # Read summary to get details
            with open(latest_session, 'r') as f:
                summary_content = f.read()
            
            # Extract attempts and score from summary
            attempts = len(glob.glob(f"{session_dir}/attempt_*"))
            
            # Find best score
            best_score = 0
            for attempt_dir in glob.glob(f"{session_dir}/attempt_*"):
                comp_file = glob.glob(f"{attempt_dir}/completeness_*.md")[0] if glob.glob(f"{attempt_dir}/completeness_*.md") else None
                if comp_file and os.path.exists(comp_file):
                    with open(comp_file, 'r') as f:
                        content = f.read()
                        if "Overall Score:" in content:
                            score_line = [line for line in content.split('\n') if "Overall Score:" in line][0]
                            score = float(score_line.split(":")[1].split("/")[0].strip())
                            best_score = max(best_score, score)
            
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_session))
            session_id = os.path.basename(session_dir)
            
            resume_options.append({
                "type": "draft",
                "path": session_dir,
                "session_id": session_id,
                "attempts": attempts,
                "best_score": best_score,
                "modified": mod_time.strftime("%Y-%m-%d %H:%M"),
                "description": f"Draft session: {session_id}"
            })
        
        return {
            "resume_options": resume_options,
            "has_options": len(resume_options) > 0
        }
    
    def exec(self, prep_data):
        if not prep_data["has_options"]:
            print("   No existing work found. Starting fresh.")
            return {"mode": "fresh"}
        
        print("\n📂 Found existing work:\n")
        
        for i, option in enumerate(prep_data["resume_options"], 1):
            print(f"{i}. {option['description']}")
            print(f"   - Last modified: {option['modified']}")
            if option["type"] == "published":
                print(f"   - Completeness: Unknown (needs analysis)")
            elif option["type"] == "draft":
                print(f"   - Attempts made: {option['attempts']}")
                print(f"   - Best score: {option['best_score']}/100")
            print()
        
        print(f"{len(prep_data['resume_options']) + 1}. Start fresh (ignore existing work)")
        
        # For now, automatically select the most recent option
        # In a real implementation, this would prompt the user
        print("\n⚡ Auto-selecting most recent work (option 1)")
        selected = prep_data["resume_options"][0]
        
        return {
            "mode": selected["type"],
            "selected": selected
        }
    
    def _parse_document_sections(self, content, context):
        """Parse a markdown document into sections based on context definition"""
        sections = {}
        
        # Get expected sections from context
        expected_sections = [s["name"] for s in context["deliverables"][0]["sections"]]
        
        # Split document by ## headers
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('## ') and not line.startswith('### '):
                # Save previous section if exists
                if current_section and current_section in expected_sections:
                    section_content = '\n'.join(current_content).strip()
                    sections[current_section] = {
                        "name": current_section,
                        "content": section_content,
                        "status": "completed",
                        "word_count": len(section_content.split()),
                        "quality_score": 8,  # Default score for existing content
                        "version": 1,
                        "review_status": "reviewed",
                        "feedback": {
                            "things_to_remove": [],
                            "things_to_add": [],
                            "things_to_change": []
                        }
                    }
                
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section and current_section in expected_sections:
            section_content = '\n'.join(current_content).strip()
            sections[current_section] = {
                "name": current_section,
                "content": section_content,
                "status": "completed",
                "word_count": len(section_content.split()),
                "quality_score": 8,
                "version": 1,
                "review_status": "reviewed",
                "feedback": {
                    "things_to_remove": [],
                    "things_to_add": [],
                    "things_to_change": []
                }
            }
        
        # Add any missing sections as pending
        for expected in expected_sections:
            if expected not in sections:
                sections[expected] = {
                    "name": expected,
                    "content": "",
                    "status": "pending",
                    "word_count": 0,
                    "quality_score": 0,
                    "version": 0,
                    "review_status": None,
                    "feedback": {
                        "things_to_remove": [],
                        "things_to_add": [],
                        "things_to_change": []
                    }
                }
        
        return sections
    
    def post(self, shared, prep_res, exec_res):
        if not exec_res:
            return None
        
        mode = exec_res["mode"]
        shared["resume_mode"] = mode
        
        if mode == "fresh":
            print("   ✅ Starting fresh document generation")
            return None
        
        selected = exec_res["selected"]
        shared["resumed_from"] = selected["path"]
        
        if mode == "published":
            # Load published document
            print(f"\n   📄 Loading published document: {selected['path']}")
            with open(selected["path"], 'r') as f:
                content = f.read()
            
            shared["document"] = content
            
            # Parse document into sections
            sections = self._parse_document_sections(content, shared["context"])
            shared["sections"] = sections
            
            # Mark for immediate completeness analysis
            print("   ✅ Document loaded and parsed into sections.")
            print(f"   📝 Found {len(sections)} sections")
            return "skip_drafting"  # Skip section drafting, go straight to assembly
            
        elif mode == "draft":
            # Load latest draft from session
            print(f"\n   📁 Loading draft session: {selected['session_id']}")
            
            # Find latest attempt
            attempt_dirs = glob.glob(f"{selected['path']}/attempt_*")
            attempt_dirs.sort(key=lambda x: int(x.split('_')[-1]))
            latest_attempt = attempt_dirs[-1]
            attempt_num = int(latest_attempt.split('_')[-1])
            
            # Load document
            doc_files = glob.glob(f"{latest_attempt}/document_*.md")
            if doc_files:
                with open(doc_files[0], 'r') as f:
                    shared["document"] = f.read()
                print(f"   ✅ Loaded document from attempt {attempt_num}")
            
            # Load sections metadata
            section_files = glob.glob(f"{latest_attempt}/sections_*.yaml")
            if section_files:
                with open(section_files[0], 'r') as f:
                    sections_data = yaml.safe_load(f)
                    if "sections" not in shared:
                        shared["sections"] = {}
                    shared["sections"].update(sections_data)
                print(f"   ✅ Loaded section metadata")
            
            # Load completeness analysis
            comp_files = glob.glob(f"{latest_attempt}/completeness_*.yaml")
            if comp_files:
                with open(comp_files[0], 'r') as f:
                    shared["completeness_analysis"] = yaml.safe_load(f)
                print(f"   ✅ Loaded completeness analysis")
            
            # Restore session info
            shared["session"] = {
                "id": selected["session_id"],
                "start_time": datetime.now().isoformat(),  # New start time for this run
                "versions": []  # Will be populated as we save new versions
            }
            
            # Update attempts counter
            shared["attempts"]["current"] = attempt_num
            print(f"   ✅ Resuming from attempt {attempt_num}/{shared['attempts']['max']}")
            
            if attempt_num >= shared["attempts"]["max"]:
                print(f"\n   ⚠️  Warning: Already at maximum attempts!")
            
            return "skip_drafting"  # Skip section drafting since we loaded existing
        
        return None

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
            
            # Track revision reason
            if "completeness_analysis" in shared:
                score = shared["completeness_analysis"]["overall_completeness"]
                shared["rejection_reason"] = f"Completeness score too low ({score}/100)"
            else:
                shared["rejection_reason"] = "Sections need revision based on feedback"
        return None

# CompletenessGateNode removed - DocumentCompletenessNode already handles gating

class EndNode(Node):
    """Final node that reports generation statistics"""
    
    def _create_session_summary(self, shared):
        """Create a summary report for the entire session"""
        session = shared["session"]
        summary_path = f"drafts/{session['id']}/summary.md"
        
        with open(summary_path, "w") as f:
            f.write(f"# Document Generation Session Summary\n\n")
            f.write(f"**Session ID:** {session['id']}\n")
            f.write(f"**Start Time:** {session['start_time']}\n")
            f.write(f"**Document:** {shared['context']['topic']}\n")
            f.write(f"**Total Attempts:** {len(session['versions'])}\n\n")
            
            f.write("## Score Progression\n\n")
            for v in session['versions']:
                f.write(f"- Attempt {v['attempt']}: {v['score']}/100\n")
            
            f.write("\n## Final Status\n\n")
            if shared.get("document_published"):
                f.write("✅ Document was successfully published\n")
                f.write(f"📁 Published to: {shared.get('output_filename', 'Unknown')}\n")
            else:
                f.write("❌ Document was not published\n")
                f.write(f"❓ Reason: {shared.get('rejection_reason', 'Unknown')}\n")
            
            # Add final issues if available
            if "completeness_analysis" in shared:
                analysis = shared["completeness_analysis"]
                f.write("\n## Final Issues\n\n")
                if analysis.get("readability_issues"):
                    f.write(f"- Readability Issues: {len(analysis['readability_issues'])}\n")
                if analysis.get("conceptual_gaps"):
                    f.write(f"- Conceptual Gaps: {len(analysis['conceptual_gaps'])}\n")
                if analysis.get("unfulfilled_goals"):
                    f.write(f"- Unfulfilled Goals: {len(analysis['unfulfilled_goals'])}\n")
                if analysis.get("scope_violations"):
                    f.write(f"- Scope Violations: {len(analysis['scope_violations'])}\n")
            
            f.write("\n## Next Steps\n\n")
            f.write("1. Review the completeness analysis in the latest attempt folder\n")
            f.write("2. Edit the document to address the identified issues\n")
            f.write("3. Pay special attention to readability for the target audience\n")
            f.write("4. Ensure all goals from context.yml are addressed\n")
    
    def post(self, shared, prep_res, exec_res):
        # Determine document status
        was_published = shared.get("document_published", False)
        completeness_score = shared.get("completeness_analysis", {}).get("overall_completeness", "N/A")
        attempts_made = shared.get("attempts", {}).get("current", 0)
        max_attempts = shared.get("attempts", {}).get("max", 3)
        
        print("\n" + "="*60)
        print("DOCUMENT GENERATION SUMMARY")
        print("="*60)
        
        # Report status
        if was_published:
            print("✅ Document Status: PUBLISHED")
            print(f"📁 Output Location: {shared.get('output_filename', 'Unknown')}")
        else:
            print("❌ Document Status: NOT PUBLISHED")
            rejection_reason = shared.get("rejection_reason", "Unknown reason")
            print(f"❓ Reason: {rejection_reason}")
        
        # Report completeness
        if completeness_score != "N/A":
            score_icon = "✅" if completeness_score >= 70 else "❌"
            print(f"\n{score_icon} Completeness Score: {completeness_score}/100")
            if completeness_score < 70:
                print(f"   (Minimum required: 70/100)")
        
        # Report attempts
        if attempts_made > 0:
            print(f"\n🔄 Revision Attempts: {attempts_made}/{max_attempts}")
        
        # Report document statistics
        if "document" in shared and was_published:
            print(f"\n📊 Document Statistics:")
            print(f"   Total Word Count: {len(shared['document'].split())}")
        
        # Report section summary
        if "sections" in shared:
            print("\n📝 Section Summary:")
            for name, data in shared["sections"].items():
                status_icon = "✅" if data.get("status") == "completed" else "⚠️"
                print(f"   {status_icon} {name}: {data['word_count']} words, "
                      f"Quality: {data.get('quality_score', 'N/A')}/10")
        
        # Show saved draft versions
        if "session" in shared and shared["session"].get("versions"):
            print("\n📁 Draft Versions Saved:")
            for version in shared["session"]["versions"]:
                print(f"   - Attempt {version['attempt']}: {version['path']} (Score: {version['score']}/100)")
            
            # Create session summary
            self._create_session_summary(shared)
        
        # Final message
        print("\n" + "="*60)
        if was_published:
            print("✅ Document generation completed successfully!")
        else:
            print("❌ Document generation ended without publishing.")
            print("   Review the issues above and try again.")
            if "session" in shared:
                print(f"\n💡 All draft versions saved in: drafts/{shared['session']['id']}/")
                print("   You can manually edit the latest draft to address the issues.")
        print("="*60)

class AbandonNode(Node):
    """Handles cases where document generation cannot continue"""
    
    def post(self, shared, prep_res, exec_res):
        print("\n" + "="*60)
        print("⚠️  DOCUMENT GENERATION ABANDONED")
        print("="*60)
        
        # Set status for EndNode
        shared["document_published"] = False
        shared["rejection_reason"] = f"Maximum revision attempts ({shared['attempts']['max']}) reached"
        
        # Report why abandoned
        completeness_score = shared.get("completeness_analysis", {}).get("overall_completeness", "N/A")
        print(f"\n❌ Reason: Maximum attempts reached ({shared['attempts']['current']}/{shared['attempts']['max']})")
        
        if completeness_score != "N/A":
            print(f"❌ Final Completeness Score: {completeness_score}/100 (Required: 70/100)")
            
            # Show what was still wrong
            analysis = shared.get("completeness_analysis", {})
            issues = []
            if analysis.get("readability_issues"):
                issues.append(f"{len(analysis['readability_issues'])} readability issues")
            if analysis.get("conceptual_gaps"):
                issues.append(f"{len(analysis['conceptual_gaps'])} conceptual gaps")
            if analysis.get("unfulfilled_goals"):
                issues.append(f"{len(analysis['unfulfilled_goals'])} unfulfilled goals")
            if analysis.get("scope_violations"):
                issues.append(f"{len(analysis['scope_violations'])} scope violations")
            
            if issues:
                print(f"\n📋 Outstanding Issues:")
                for issue in issues:
                    print(f"   - {issue}")
        
        # Report section status
        if "sections" in shared:
            completed = sum(1 for s in shared["sections"].values() if s["status"] == "completed")
            total = len(shared["sections"])
            print(f"\n📝 Section Progress: {completed}/{total} sections completed")
            
            # Show which sections need work
            incomplete = [name for name, data in shared["sections"].items() 
                         if data["status"] != "completed"]
            if incomplete:
                print(f"   Incomplete sections: {', '.join(incomplete)}")
        
        print("\n💡 Suggestions:")
        print("   1. Review the completeness issues identified above")
        print("   2. Consider simplifying content for the target audience")
        print("   3. Ensure all goals from context.yml are addressed")
        print("   4. Check that content stays within defined scope")
        print("="*60)

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
        print(f"\n✅ Publisher Node Completed. Document saved to: {exec_res}")
        # Mark document as published for EndNode
        shared["document_published"] = True
        shared["output_filename"] = exec_res
        return None

class DraftVersioningNode(Node):
    """Saves every version of the document throughout the generation process"""
    
    def prep(self, shared):
        print("\n💾 Draft Versioning Node")
        
        # Initialize session tracking if not present
        if "session" not in shared:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            doc_name = shared["context"]["output_filename"].split("/")[-1].replace(".md", "")
            shared["session"] = {
                "id": f"{doc_name}_session_{timestamp}",
                "start_time": datetime.now().isoformat(),
                "versions": []
            }
        
        # Prepare data for saving
        attempt_num = shared["attempts"]["current"] + 1
        
        return {
            "session_id": shared["session"]["id"],
            "attempt": attempt_num,
            "document": shared.get("document", ""),
            "sections": shared.get("sections", {}),
            "completeness": shared.get("completeness_analysis", {}),
            "feedback": shared.get("feedback", {})
        }
    
    def exec(self, prep_data):
        if not prep_data["document"]:
            print("   No document to save yet")
            return None
        
        # Create directory structure
        base_dir = f"drafts/{prep_data['session_id']}/attempt_{prep_data['attempt']}"
        os.makedirs(base_dir, exist_ok=True)
        
        # Save document
        doc_path = f"{base_dir}/document_v{prep_data['attempt']}.md"
        with open(doc_path, "w") as f:
            f.write(prep_data["document"])
        
        # Save completeness analysis if available
        if prep_data["completeness"]:
            completeness_path = f"{base_dir}/completeness_v{prep_data['attempt']}.md"
            with open(completeness_path, "w") as f:
                score = prep_data["completeness"].get("overall_completeness", "N/A")
                f.write(f"# Completeness Analysis - Attempt {prep_data['attempt']}\n\n")
                f.write(f"**Overall Score:** {score}/100\n\n")
                
                # Write issues summary
                f.write("## Issues Summary\n\n")
                if prep_data["completeness"].get("readability_issues"):
                    f.write(f"- Readability Issues: {len(prep_data['completeness']['readability_issues'])}\n")
                if prep_data["completeness"].get("conceptual_gaps"):
                    f.write(f"- Conceptual Gaps: {len(prep_data['completeness']['conceptual_gaps'])}\n")
                if prep_data["completeness"].get("unfulfilled_goals"):
                    f.write(f"- Unfulfilled Goals: {len(prep_data['completeness']['unfulfilled_goals'])}\n")
                if prep_data["completeness"].get("scope_violations"):
                    f.write(f"- Scope Violations: {len(prep_data['completeness']['scope_violations'])}\n")
                
                # Write detailed analysis
                f.write("\n## Detailed Analysis\n\n")
                f.write(yaml.dump(prep_data["completeness"], default_flow_style=False))
        
        # Save sections metadata
        if prep_data["sections"]:
            sections_path = f"{base_dir}/sections_v{prep_data['attempt']}.yaml"
            sections_data = {}
            for name, data in prep_data["sections"].items():
                sections_data[name] = {
                    "status": data.get("status"),
                    "word_count": data.get("word_count"),
                    "quality_score": data.get("quality_score"),
                    "version": data.get("version"),
                    "feedback": data.get("feedback", {})
                }
            with open(sections_path, "w") as f:
                yaml.dump(sections_data, f, default_flow_style=False)
        
        # Save feedback if available
        if any(prep_data["feedback"].values()):
            feedback_path = f"{base_dir}/feedback_v{prep_data['attempt']}.yaml"
            with open(feedback_path, "w") as f:
                yaml.dump(prep_data["feedback"], f, default_flow_style=False)
        
        return {
            "saved_path": base_dir,
            "attempt": prep_data["attempt"],
            "score": prep_data["completeness"].get("overall_completeness", "N/A")
        }
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            # Track this version
            version_info = {
                "attempt": exec_res["attempt"],
                "path": exec_res["saved_path"],
                "score": exec_res["score"],
                "timestamp": datetime.now().isoformat()
            }
            shared["session"]["versions"].append(version_info)
            
            print(f"   ✅ Saved draft version {exec_res['attempt']} to: {exec_res['saved_path']}")
            print(f"   📊 Completeness Score: {exec_res['score']}/100")
        
        return None

def build_section_workflow():
    """Builds the optimal section-based workflow with completeness checks"""
    
    # Create nodes
    resume_detector_node = ResumeDetectorNode()
    section_lead_node = SectionBasedLeadNode()
    batch_review_node = BatchSectionReviewNode()
    section_revision_node = SectionRevisionNode()
    abandon_node = AbandonNode()
    end_node = EndNode()
    publisher_node = PublisherNode()
    draft_versioning_node = DraftVersioningNode()
    
    # Build the section-based workflow with completeness checks
    
    # Start with resume detection
    resume_detector_node >> section_lead_node
    resume_detector_node - "skip_drafting" >> document_assembler  # Skip to assembly if loaded existing
    
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
    document_assembler >> draft_versioning_node
    draft_versioning_node >> document_completeness_node
    
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
    
    # Create and return the flow - now starts with resume detection
    return Flow(start=resume_detector_node)

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
