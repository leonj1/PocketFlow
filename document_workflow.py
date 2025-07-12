#!/usr/bin/env python3
"""
Document Approval Workflow using PocketFlow

This script implements a comprehensive document creation and approval workflow
that reads context from a YAML file and guides the document through multiple
stages of drafting, review, and approval.
"""

import yaml
import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os
sys.path.append(str(Path(__file__).parent))

from pocketflow import Node, Flow, BaseNode
from document_ai_agents import DocumentAiAgent, get_document_ai_agent


# Base Classes
class DocumentNode(Node):
    """Base class for all document workflow nodes."""
    
    def get_context(self, shared: Dict) -> Dict:
        """Get document context from shared state."""
        return shared.get("context", {})
    
    def get_document(self, shared: Dict) -> Dict:
        """Get current document from shared state."""
        return shared.get("document", {})
    
    def update_document(self, shared: Dict, updates: Dict) -> None:
        """Update document in shared state."""
        if "document" not in shared:
            shared["document"] = {}
        shared["document"].update(updates)
    
    def add_audit_entry(self, shared: Dict, action: str, details: str) -> None:
        """Add entry to audit trail."""
        if "audit_trail" not in shared:
            shared["audit_trail"] = []
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "node": self.__class__.__name__,
            "action": action,
            "details": details
        }
        shared["audit_trail"].append(entry)
    
    def format_output(self, title: str, content: str) -> None:
        """Format output for CLI display."""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        print(content)
        print(f"{'='*60}\n")


class ReviewNode(DocumentNode):
    """Base class for review nodes."""
    
    def collect_feedback(self, prompt: str, options: List[str] = None) -> str:
        """Collect feedback from user."""
        print(f"\n{prompt}")
        
        if options:
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            while True:
                try:
                    choice = int(input("\nEnter your choice: "))
                    if 1 <= choice <= len(options):
                        return options[choice - 1]
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a number.")
        else:
            return input("\nYour input: ")
    
    def collect_detailed_feedback(self) -> Dict:
        """Collect detailed feedback for document revision."""
        feedback = {
            "overall": self.collect_feedback("Overall feedback:", 
                                           ["Approve", "Needs Minor Revision", "Needs Major Revision", "Reject"]),
            "comments": input("Additional comments (optional): "),
            "specific_issues": []
        }
        
        if feedback["overall"] in ["Needs Minor Revision", "Needs Major Revision"]:
            add_more = True
            while add_more:
                issue = input("Describe a specific issue (or press Enter to finish): ")
                if issue:
                    feedback["specific_issues"].append(issue)
                else:
                    add_more = False
        
        return feedback


class ApprovalNode(ReviewNode):
    """Base class for approval nodes."""
    
    def check_approval_criteria(self, shared: Dict) -> bool:
        """Check if approval criteria are met based on context."""
        context = self.get_context(shared)
        
        # This is a simplified check - in real implementation would be more complex
        return True
    
    def record_approval(self, shared: Dict, approver: str, decision: str, comments: str = "") -> None:
        """Record approval decision."""
        if "approvals" not in shared:
            shared["approvals"] = []
        
        approval = {
            "timestamp": datetime.datetime.now().isoformat(),
            "approver": approver,
            "decision": decision,
            "comments": comments,
            "node": self.__class__.__name__
        }
        shared["approvals"].append(approval)
        self.add_audit_entry(shared, "approval_recorded", f"{approver}: {decision}")


# Context Loading
class ContextLoaderNode(DocumentNode):
    """Load and validate context from YAML file."""
    
    def prep(self, shared):
        return self.params
    
    def exec(self, prep_res):
        prep_res = prep_res or {}
        context_path = prep_res.get("context_path", "context.yml")
        
        try:
            with open(context_path, 'r') as f:
                context = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ["topic", "purpose", "audience", "scope", "deliverables"]
            missing_fields = [field for field in required_fields if field not in context]
            
            if missing_fields:
                raise ValueError(f"Missing required fields in context: {missing_fields}")
            
            self.format_output("Context Loaded Successfully", 
                             f"Topic: {context['topic']}\n"
                             f"Document Type: {context.get('document_type', 'Standard')}\n"
                             f"Purpose: {context['purpose']}")
            
            return {"context": context, "status": "success"}
            
        except Exception as e:
            self.format_output("Error Loading Context", str(e))
            return {"status": "error", "message": str(e)}
    
    def post(self, shared, prep_res, exec_res):
        if exec_res["status"] == "success":
            shared["context"] = exec_res["context"]
            shared["document"] = {
                "title": exec_res["context"]["topic"],
                "type": exec_res["context"].get("document_type", "Standard"),
                "version": "0.1",
                "status": "initialized",
                "content": {},
                "metadata": {
                    "created": datetime.datetime.now().isoformat(),
                    "last_modified": datetime.datetime.now().isoformat()
                }
            }
            self.add_audit_entry(shared, "context_loaded", f"Loaded context for: {shared['context']['topic']}")
            return None  # Continue to next node
        else:
            return "error"


# Initialization Phase Nodes
class NeedsAssessmentNode(ReviewNode):
    """Assess needs based on context and gather additional requirements."""
    
    def __init__(self):
        super().__init__()
        # Initialize AI agent if enabled
        try:
            self.ai_agent = get_document_ai_agent()
            self.ai_enabled = self.ai_agent.is_enabled()
        except Exception as e:
            print(f"AI Agent initialization failed: {e}")
            self.ai_agent = None
            self.ai_enabled = False
    
    def exec(self, prep_res):
        return {"assessed_needs": []}
    
    def post(self, shared, prep_res, exec_res):
        context = self.get_context(shared)
        
        self.format_output("Needs Assessment", 
                         f"Analyzing requirements for: {context['topic']}\n\n"
                         f"Audience:\n{self._format_audience(context['audience'])}\n"
                         f"Scope: {len(context['scope']['includes'])} items included\n"
                         f"Timeline: {context['constraints']['timeline']}")
        
        # Search for similar standards to inform needs assessment
        search_results = []
        if self.ai_agent:
            try:
                print("\n🔍 Searching for similar standards and best practices...")
                search_results = self.ai_agent.search_similar_standards(context)
                if search_results:
                    print(f"  ✓ Found {len(search_results)} relevant standards")
                    # Display top results
                    for i, result in enumerate(search_results[:3]):
                        print(f"    {i+1}. {result.title}")
            except Exception as e:
                print(f"  ⚠️  Search failed: {e}")
        
        # AI-powered needs assessment if enabled
        if self.ai_enabled and self.ai_agent:
            try:
                print("\n🤖 Running AI needs assessment...")
                ai_assessment = self.ai_agent.assess_needs(context)
                
                # Display AI assessment
                self.format_output("AI Needs Assessment",
                                 f"Identified Needs:\n" + "\n".join(f"  • {n}" for n in ai_assessment.identified_needs) + "\n\n"
                                 f"Priority Areas:\n" + "\n".join(f"  • {p}" for p in ai_assessment.priority_areas) + "\n\n"
                                 f"Potential Challenges:\n" + "\n".join(f"  • {c}" for c in ai_assessment.potential_challenges) + "\n\n"
                                 f"Recommended Approach: {ai_assessment.recommended_approach}")
                
                needs = ai_assessment.identified_needs
                
                # Add insights from search results if available
                if search_results:
                    self.format_output("Related Standards Found",
                                     "\n".join(f"• {r.title}\n  {r.snippet}\n  URL: {r.url}" 
                                              for r in search_results[:3]))
                
            except Exception as e:
                print(f"\n⚠️  AI assessment failed: {e}")
                print(f"     Error details: {type(e).__name__}: {str(e)}")
                # Log more details about the AI configuration
                if self.ai_agent:
                    config = self.ai_agent.get_config()
                    print(f"     AI Config: Model={config.get('model')}, Provider={config.get('provider')}, Enabled={config.get('enabled')}")
                # Fallback to default needs
                needs = [
                    "Clear examples for each security pattern",
                    "Integration guides for existing systems",
                    "Migration path from current practices",
                    "Performance impact analysis"
                ]
        else:
            # Default needs when AI is disabled
            needs = [
                "Clear examples for each security pattern",
                "Integration guides for existing systems",
                "Migration path from current practices",
                "Performance impact analysis"
            ]
        
        confirm = self.collect_feedback("Are there additional needs to address?", ["Yes", "No"])
        
        if confirm == "Yes":
            additional = input("Please describe additional needs: ")
            needs.append(additional)
        
        self.update_document(shared, {"assessed_needs": needs})
        # Store search results in shared state for use by other nodes
        if search_results:
            shared["search_results_standards"] = [r.to_dict() for r in search_results]
        self.add_audit_entry(shared, "needs_assessed", f"Identified {len(needs)} needs")
        
        return None  # Continue to next node
    
    def _format_audience(self, audience: Dict) -> str:
        """Format audience information for display."""
        lines = []
        for aud_type, members in audience.items():
            lines.append(f"  {aud_type.capitalize()}:")
            for member in members:
                lines.append(f"    - {member['role']} ({member.get('experience_level', 'All')})")
        return "\n".join(lines)


class OutlineTemplateNode(DocumentNode):
    """Generate document outline based on context and deliverables."""
    
    def __init__(self):
        super().__init__()
        # Initialize AI agent if enabled
        try:
            self.ai_agent = get_document_ai_agent()
            self.ai_enabled = self.ai_agent.is_enabled()
        except Exception as e:
            print(f"AI Agent initialization failed: {e}")
            self.ai_agent = None
            self.ai_enabled = False
    
    def exec(self, prep_res):
        return {"outline": []}
    
    def post(self, shared, prep_res, exec_res):
        context = self.get_context(shared)
        document = self.get_document(shared)
        needs = document.get("assessed_needs", [])
        
        # Search for document templates
        template_results = []
        if self.ai_agent:
            try:
                print("\n🔍 Searching for document structure templates...")
                template_results = self.ai_agent.search_document_templates(context)
                if template_results:
                    print(f"  ✓ Found {len(template_results)} document templates")
                    for i, template in enumerate(template_results[:3]):
                        print(f"    {i+1}. {template.title}")
            except Exception as e:
                print(f"  ⚠️  Template search failed: {e}")
        
        # Try AI-powered outline generation
        if self.ai_enabled and self.ai_agent:
            try:
                print("\n🤖 Generating AI-powered outline...")
                ai_outline = self.ai_agent.generate_outline(context, needs)
                
                # Convert AI outline to our format
                outline = []
                for section in ai_outline.sections:
                    outline.append({
                        "name": section.get("name", "Untitled Section"),
                        "max_pages": section.get("max_pages", 5),
                        "audience_focus": section.get("audience_focus", ["All"]),
                        "content": "",
                        "status": "pending"
                    })
                
                print(f"  ✓ AI generated outline with {len(outline)} sections")
                print(f"  📄 {ai_outline.structure_notes}")
                
            except Exception as e:
                print(f"\n⚠️  AI outline generation failed: {e}")
                outline = None
        else:
            outline = None
        
        # Fallback to context-based outline if AI fails or is disabled
        if not outline:
            deliverables = context.get("deliverables", [])
            
            # Find main document deliverable
            main_doc = next((d for d in deliverables if d["type"] == "Main Document"), None)
            
            if not main_doc:
                self.add_audit_entry(shared, "outline_error", "No main document found in deliverables")
                return "error"
            
            # Generate outline from sections
            outline = []
            for section in main_doc["sections"]:
                outline.append({
                    "name": section["name"],
                    "max_pages": section.get("max_pages", 5),
                    "audience_focus": section.get("audience_focus", ["All"]),
                    "content": "",
                    "status": "pending"
                })
        
        self.format_output("Document Outline Generated",
                         "\n".join([f"{i+1}. {s['name']} ({s['max_pages']} pages max)" 
                                   for i, s in enumerate(outline)]))
        
        self.update_document(shared, {"outline": outline})
        # Store template search results in shared state
        if template_results:
            shared["search_results_templates"] = [t.to_dict() for t in template_results]
        self.add_audit_entry(shared, "outline_generated", f"Created outline with {len(outline)} sections")
        
        return None  # Continue to next node


class RoleAssignmentNode(DocumentNode):
    """Assign roles based on stakeholders defined in context."""
    
    def exec(self, prep_res):
        return {"assignments": {}}
    
    def post(self, shared, prep_res, exec_res):
        context = self.get_context(shared)
        stakeholders = context.get("stakeholders", {})
        
        assignments = {
            "lead_author": "System (AI-assisted)",
            "reviewers": [],
            "approvers": []
        }
        
        # Extract reviewers
        for reviewer_group in stakeholders.get("reviewers", []):
            if isinstance(reviewer_group, dict):
                assignments["reviewers"].append(reviewer_group["group"])
            else:
                assignments["reviewers"].append(reviewer_group)
        
        # Extract approvers
        for approver_group in stakeholders.get("approvers", []):
            assignments["approvers"].append(approver_group["name"])
        
        self.format_output("Role Assignments",
                         f"Lead Author: {assignments['lead_author']}\n"
                         f"Reviewers: {', '.join(assignments['reviewers'])}\n"
                         f"Approvers: {', '.join(assignments['approvers'])}")
        
        shared["assignments"] = assignments
        self.add_audit_entry(shared, "roles_assigned", 
                           f"Assigned {len(assignments['reviewers'])} reviewers, "
                           f"{len(assignments['approvers'])} approvers")
        
        return None  # Continue to next node


# Working Group Flow Nodes
class DocumentDraftingNode(DocumentNode):
    """Draft document sections based on outline and context."""
    
    def __init__(self):
        super().__init__()
        # Initialize AI agent if enabled
        try:
            self.ai_agent = get_document_ai_agent()
            self.ai_enabled = self.ai_agent.is_enabled()
        except Exception as e:
            print(f"AI Agent initialization failed: {e}")
            self.ai_agent = None
            self.ai_enabled = False
    
    def exec(self, prep_res):
        return {"draft_complete": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        context = self.get_context(shared)
        outline = document.get("outline", [])
        
        self.format_output("Document Drafting", 
                         f"Drafting {len(outline)} sections for: {document['title']}")
        
        # Track previously generated sections for context
        previous_sections = []
        
        # Draft each section
        for i, section in enumerate(outline):
            if section["status"] == "pending":
                print(f"\nDrafting section {i+1}: {section['name']}")
                
                if self.ai_enabled and self.ai_agent:
                    # Use AI to generate content
                    try:
                        # Search for references specific to this section
                        section_references = []
                        if self.ai_agent:
                            try:
                                print("  🔍 Searching for section references...")
                                section_references = self.ai_agent.search_references(section['name'], context)
                                if section_references:
                                    print(f"    ✓ Found {len(section_references)} references")
                                    for j, ref in enumerate(section_references[:2]):
                                        print(f"      {j+1}. {ref.title}")
                            except Exception as e:
                                print(f"    ⚠️  Reference search failed: {e}")
                        
                        print("  Using AI to generate content...")
                        
                        # Generate section with AI
                        section_result = self.ai_agent.generate_section(
                            section_name=section['name'],
                            context=context,
                            max_pages=section.get('max_pages', 5),
                            previous_sections=previous_sections
                        )
                        
                        section["content"] = section_result.content
                        section["key_points"] = section_result.key_points
                        section["ai_generated"] = True
                        
                        # Store references found for this section
                        if section_references:
                            section["references"] = [ref.to_dict() for ref in section_references[:3]]
                        
                        # Add summary to previous sections
                        summary = f"{section['name']}: {', '.join(section_result.key_points[:3])}"
                        previous_sections.append(summary)
                        
                        print(f"  ✓ AI generated {len(section_result.content.split())} words")
                        
                    except Exception as e:
                        print(f"  ✗ AI generation failed: {e}")
                        print(f"     Error details: {type(e).__name__}: {str(e)}")
                        # Log more details about the AI configuration
                        if self.ai_agent:
                            config = self.ai_agent.get_config()
                            print(f"     AI Config: Model={config.get('model')}, Provider={config.get('provider')}, Enabled={config.get('enabled')}")
                        # Fallback to placeholder
                        content = self._generate_placeholder_content(section, context)
                        section["content"] = content
                        section["ai_generated"] = False
                else:
                    # Use placeholder content when AI is disabled
                    content = self._generate_placeholder_content(section, context)
                    section["content"] = content
                    section["ai_generated"] = False
                
                section["status"] = "drafted"
                section["draft_version"] = 1
                section["last_modified"] = datetime.datetime.now().isoformat()
        
        self.update_document(shared, {
            "outline": outline,
            "status": "drafted",
            "version": "0.2"
        })
        
        self.add_audit_entry(shared, "document_drafted", f"Completed draft of {len(outline)} sections")
        
        # Check if we're revising based on feedback
        if shared.get("revision_needed", False):
            print("\nIncorporating feedback into revision...")
            shared["revision_needed"] = False
            return "revised"
        
        return None  # Continue to peer review
    
    def _generate_placeholder_content(self, section: Dict, context: Dict) -> str:
        """Generate placeholder content when AI is not available."""
        if section["name"] == "Executive Summary":
            content = f"""This document establishes standards for {context['topic']}.
                    
Purpose: {context['purpose']}

Key Requirements:
- Authentication using OAuth 2.0 and JWT
- Role-based authorization (RBAC)
- Comprehensive input validation
- Rate limiting for all endpoints
"""
        else:
            content = f"[Content for {section['name']} - {section['max_pages']} pages]\n"
            content += f"Audience: {', '.join(section['audience_focus'])}\n"
            content += f"[Manual content required - AI disabled or unavailable]"
        
        return content


class PeerReviewNode(ReviewNode):
    """Conduct peer review of drafted document."""
    
    def exec(self, prep_res):
        return {"review_complete": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        
        self.format_output("Peer Review", 
                         f"Document: {document['title']} (v{document['version']})\n"
                         f"Status: {document['status']}")
        
        # Show document sections for review
        print("\nDocument Sections:")
        for i, section in enumerate(document["outline"]):
            print(f"\n{i+1}. {section['name']}")
            print("-" * 40)
            print(section["content"][:200] + "..." if len(section["content"]) > 200 else section["content"])
        
        # Collect feedback
        feedback = self.collect_detailed_feedback()
        
        # Store feedback
        if "reviews" not in shared:
            shared["reviews"] = []
        
        review_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "reviewer": "Peer Reviewer",
            "feedback": feedback,
            "version_reviewed": document["version"]
        }
        shared["reviews"].append(review_record)
        
        self.add_audit_entry(shared, "peer_review_completed", 
                           f"Review decision: {feedback['overall']}")
        
        # Determine next action
        if feedback["overall"] == "Approve":
            return "approved"
        elif feedback["overall"] in ["Needs Minor Revision", "Needs Major Revision"]:
            shared["revision_needed"] = True
            shared["revision_feedback"] = feedback
            return "needs_revision"
        else:
            return "rejected"
    
    def _compile_document_content(self, document: Dict) -> str:
        """Compile all document sections into a single string for review."""
        content_parts = []
        
        # Add title and metadata
        content_parts.append(f"Title: {document.get('title', 'Untitled')}")
        content_parts.append(f"Version: {document.get('version', '0.1')}")
        content_parts.append(f"Type: {document.get('type', 'Document')}")
        content_parts.append("\n" + "="*60 + "\n")
        
        # Add all sections
        for section in document.get("outline", []):
            if section.get("status") == "drafted":
                content_parts.append(f"\n## {section['name']}\n")
                content_parts.append(section.get("content", "[No content]"))
                
                # Add key points if available
                if section.get("key_points"):
                    content_parts.append("\nKey Points:")
                    for point in section["key_points"]:
                        content_parts.append(f"  • {point}")
                
                content_parts.append("\n")
        
        return "\n".join(content_parts)


class VersionControlNode(DocumentNode):
    """Save document version and track changes."""
    
    def exec(self, prep_res):
        return {"version_saved": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        
        # Create version record
        if "versions" not in shared:
            shared["versions"] = []
        
        version_record = {
            "version": document["version"],
            "timestamp": datetime.datetime.now().isoformat(),
            "status": document["status"],
            "changes": shared.get("revision_feedback", {}).get("specific_issues", []),
            "outline_snapshot": json.dumps(document["outline"])
        }
        
        shared["versions"].append(version_record)
        
        # Increment version
        major, minor = document["version"].split(".")
        document["version"] = f"{major}.{int(minor) + 1}"
        
        self.format_output("Version Control",
                         f"Saved version: {version_record['version']}\n"
                         f"New version: {document['version']}\n"
                         f"Total versions: {len(shared['versions'])}")
        
        self.add_audit_entry(shared, "version_saved", 
                           f"Saved v{version_record['version']}, created v{document['version']}")
        
        return None  # Continue to next node


class WorkingGroupApprovalNode(ApprovalNode):
    """Working group approval before committee submission."""
    
    def exec(self, prep_res):
        return {"approval_decision": None}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        
        self.format_output("Working Group Approval",
                         f"Seeking approval for: {document['title']} (v{document['version']})")
        
        # Show summary of reviews
        reviews = shared.get("reviews", [])
        if reviews:
            print("\nReview History:")
            for review in reviews[-3:]:  # Show last 3 reviews
                print(f"- {review['timestamp']}: {review['feedback']['overall']}")
        
        # Collect approval decision
        decision = self.collect_feedback("Working Group Decision:", 
                                       ["Approve for Committee", "Needs More Work", "Reject"])
        
        comments = ""
        if decision != "Approve for Committee":
            comments = input("Please provide comments: ")
        
        self.record_approval(shared, "Working Group", decision, comments)
        
        if decision == "Approve for Committee":
            document["status"] = "approved_by_working_group"
            shared["working_group_approved"] = True
            return "approved"
        elif decision == "Needs More Work":
            shared["revision_needed"] = True
            return "needs_work"
        else:
            return "rejected"


# Committee Flow Nodes
class SubmissionNode(DocumentNode):
    """Submit document to committee."""
    
    def exec(self, prep_res):
        return {"submitted": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        context = self.get_context(shared)
        
        # Prepare submission package
        submission = {
            "document_title": document["title"],
            "version": document["version"],
            "submission_date": datetime.datetime.now().isoformat(),
            "working_group_approval": next(
                (a for a in reversed(shared.get("approvals", [])) 
                 if a["approver"] == "Working Group"), None
            ),
            "review_summary": len(shared.get("reviews", [])),
            "target_committee": context["stakeholders"]["approvers"][0]["name"]
        }
        
        shared["committee_submission"] = submission
        
        self.format_output("Committee Submission",
                         f"Document: {submission['document_title']}\n"
                         f"Version: {submission['version']}\n"
                         f"Target: {submission['target_committee']}\n"
                         f"Reviews completed: {submission['review_summary']}")
        
        self.add_audit_entry(shared, "submitted_to_committee", 
                           f"Submitted v{submission['version']} to {submission['target_committee']}")
        
        shared["committee_submitted"] = True
        return None  # Continue to committee review


class CommitteeReviewNode(ReviewNode):
    """Committee review of submitted document."""
    
    def exec(self, prep_res):
        return {"review_complete": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        submission = shared.get("committee_submission", {})
        
        self.format_output("Committee Review",
                         f"Reviewing: {document['title']} (v{document['version']})\n"
                         f"Committee: {submission.get('target_committee', 'Committee')}")
        
        # Simulate committee review
        print("\nCommittee reviewing document for:")
        print("- Alignment with organizational standards")
        print("- Technical accuracy and completeness")
        print("- Security requirements coverage")
        print("- Implementation feasibility")
        
        # Collect committee feedback
        decision = self.collect_feedback("Committee Decision:",
                                       ["Approve", "Clarification Needed", "Reject"])
        
        committee_feedback = {
            "decision": decision,
            "comments": input("Committee comments: ") if decision != "Approve" else "",
            "clarifications_needed": []
        }
        
        if decision == "Clarification Needed":
            print("\nWhat clarifications are needed?")
            while True:
                clarification = input("Add clarification request (or press Enter to finish): ")
                if clarification:
                    committee_feedback["clarifications_needed"].append(clarification)
                else:
                    break
        
        # Store committee feedback
        if "committee_reviews" not in shared:
            shared["committee_reviews"] = []
        
        committee_feedback["timestamp"] = datetime.datetime.now().isoformat()
        committee_feedback["version_reviewed"] = document["version"]
        shared["committee_reviews"].append(committee_feedback)
        
        self.add_audit_entry(shared, "committee_review_completed", 
                           f"Committee decision: {decision}")
        
        if decision == "Approve":
            return "approved"
        elif decision == "Clarification Needed":
            shared["clarifications_needed"] = committee_feedback["clarifications_needed"]
            return "clarification_needed"
        else:
            return "rejected"


class ClarificationNode(DocumentNode):
    """Handle clarification requests from committee."""
    
    def exec(self, prep_res):
        return {"clarifications_provided": False}
    
    def post(self, shared, prep_res, exec_res):
        clarifications = shared.get("clarifications_needed", [])
        
        self.format_output("Clarification Requests",
                         f"The committee has requested {len(clarifications)} clarifications")
        
        responses = []
        for i, clarification in enumerate(clarifications, 1):
            print(f"\n{i}. {clarification}")
            response = input("Your response: ")
            responses.append({
                "request": clarification,
                "response": response
            })
        
        # Store clarification responses
        shared["clarification_responses"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "responses": responses
        }
        
        self.add_audit_entry(shared, "clarifications_provided", 
                           f"Responded to {len(responses)} clarification requests")
        
        # Clear clarifications needed
        shared["clarifications_needed"] = []
        
        return "clarifications_provided"


class CommitteeApprovalNode(ApprovalNode):
    """Final committee approval decision."""
    
    def exec(self, prep_res):
        return {"final_decision": None}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        context = self.get_context(shared)
        committee_name = context["stakeholders"]["approvers"][0]["name"]
        approval_type = context["stakeholders"]["approvers"][0]["approval_type"]
        
        self.format_output("Committee Final Approval",
                         f"Committee: {committee_name}\n"
                         f"Approval Type Required: {approval_type}\n"
                         f"Document: {document['title']} (v{document['version']})")
        
        # Show clarification responses if any
        if "clarification_responses" in shared:
            print("\nClarifications have been provided.")
        
        # Collect final decision
        decision = self.collect_feedback(f"{committee_name} Final Decision:",
                                       ["Approve", "Reject"])
        
        if decision == "Approve" and approval_type == "unanimous":
            print("\nConfirming unanimous approval...")
            confirm = self.collect_feedback("Do all committee members approve?", ["Yes", "No"])
            if confirm == "No":
                decision = "Reject"
                print("Unanimous approval not achieved.")
        
        self.record_approval(shared, committee_name, decision)
        
        if decision == "Approve":
            document["status"] = "approved_by_committee"
            self.add_audit_entry(shared, "committee_approved", 
                               f"{committee_name} approved the document")
            return "approved"
        else:
            self.add_audit_entry(shared, "committee_rejected", 
                               f"{committee_name} rejected the document")
            return "rejected"


# Finalization Phase Nodes
class PublicationNode(DocumentNode):
    """Publish approved document in required formats."""
    
    def exec(self, prep_res):
        return {"published": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        context = self.get_context(shared)
        deliverables = context.get("deliverables", [])
        
        self.format_output("Document Publication",
                         f"Publishing: {document['title']} (v{document['version']})")
        
        published_items = []
        
        for deliverable in deliverables:
            print(f"\nGenerating: {deliverable['type']} ({deliverable['format']})")
            
            if deliverable["type"] == "Main Document":
                # Simulate PDF generation
                filename = f"{document['title'].replace(' ', '_')}_v{document['version']}.pdf"
                published_items.append({
                    "type": deliverable["type"],
                    "format": deliverable["format"],
                    "filename": filename,
                    "location": f"/published/{filename}"
                })
                print(f"✓ Generated: {filename}")
            
            elif deliverable["type"] == "Quick Reference Card":
                filename = f"{document['title'].replace(' ', '_')}_QuickRef.pdf"
                published_items.append({
                    "type": deliverable["type"],
                    "format": deliverable["format"],
                    "filename": filename,
                    "location": f"/published/{filename}"
                })
                print(f"✓ Generated: {filename}")
        
        shared["published_items"] = published_items
        document["status"] = "published"
        document["published_date"] = datetime.datetime.now().isoformat()
        
        self.add_audit_entry(shared, "document_published", 
                           f"Published {len(published_items)} deliverables")
        
        shared["published"] = True
        return None  # Continue to training


class TrainingImplementationNode(DocumentNode):
    """Plan and track training implementation."""
    
    def exec(self, prep_res):
        return {"training_planned": False}
    
    def post(self, shared, prep_res, exec_res):
        context = self.get_context(shared)
        
        self.format_output("Training Implementation",
                         "Planning training rollout for the new document")
        
        # Create training plan based on audience
        training_plan = {
            "sessions": [],
            "materials_needed": ["Slides", "Workshop Guide", "Hands-on Examples"],
            "target_completion": "30 days"
        }
        
        # Plan sessions for each audience group
        for audience_type, groups in context["audience"].items():
            for group in groups:
                session = {
                    "audience": group["role"],
                    "duration": "2 hours" if audience_type == "primary" else "1 hour",
                    "format": "Workshop" if audience_type == "primary" else "Presentation",
                    "scheduled": False
                }
                training_plan["sessions"].append(session)
        
        print(f"\nTraining Plan Created:")
        print(f"- {len(training_plan['sessions'])} sessions planned")
        print(f"- Materials: {', '.join(training_plan['materials_needed'])}")
        print(f"- Target completion: {training_plan['target_completion']}")
        
        shared["training_plan"] = training_plan
        self.add_audit_entry(shared, "training_planned", 
                           f"Created plan for {len(training_plan['sessions'])} training sessions")
        
        return None  # Continue to next node


class MaintenanceReviewNode(DocumentNode):
    """Set up maintenance and review cycle."""
    
    def exec(self, prep_res):
        return {"maintenance_configured": False}
    
    def post(self, shared, prep_res, exec_res):
        context = self.get_context(shared)
        maintenance = context.get("maintenance", {})
        
        self.format_output("Maintenance Setup",
                         f"Configuring maintenance for document lifecycle")
        
        # Set up maintenance schedule
        maintenance_schedule = {
            "review_frequency": maintenance.get("review_frequency", "Quarterly"),
            "next_review": self._calculate_next_review(maintenance.get("review_frequency", "Quarterly")),
            "owner": maintenance.get("ownership", "Document Owner"),
            "update_triggers": maintenance.get("update_triggers", []),
            "archive_policy": maintenance.get("archive_policy", "Keep last 3 versions")
        }
        
        print(f"\nMaintenance Schedule:")
        print(f"- Review Frequency: {maintenance_schedule['review_frequency']}")
        print(f"- Next Review: {maintenance_schedule['next_review']}")
        print(f"- Owner: {maintenance_schedule['owner']}")
        print(f"- Update Triggers: {len(maintenance_schedule['update_triggers'])} defined")
        
        shared["maintenance_schedule"] = maintenance_schedule
        self.add_audit_entry(shared, "maintenance_configured", 
                           f"Set up {maintenance_schedule['review_frequency']} review cycle")
        
        return None  # Continue to next node
    
    def _calculate_next_review(self, frequency: str) -> str:
        """Calculate next review date based on frequency."""
        from datetime import timedelta
        
        today = datetime.datetime.now()
        if frequency == "Quarterly":
            next_date = today + timedelta(days=90)
        elif frequency == "Monthly":
            next_date = today + timedelta(days=30)
        elif frequency == "Annually":
            next_date = today + timedelta(days=365)
        else:
            next_date = today + timedelta(days=90)  # Default to quarterly
        
        return next_date.strftime("%Y-%m-%d")


class ArchivingNode(DocumentNode):
    """Archive document and close workflow."""
    
    def exec(self, prep_res):
        return {"archived": False}
    
    def post(self, shared, prep_res, exec_res):
        document = self.get_document(shared)
        
        # Create archive record
        archive_record = {
            "document_title": document["title"],
            "final_version": document["version"],
            "published_date": document.get("published_date"),
            "total_reviews": len(shared.get("reviews", [])),
            "total_versions": len(shared.get("versions", [])),
            "audit_trail_entries": len(shared.get("audit_trail", [])),
            "archived_date": datetime.datetime.now().isoformat(),
            "archive_location": f"/archive/{document['title'].replace(' ', '_')}_v{document['version']}"
        }
        
        self.format_output("Document Archived",
                         f"Title: {archive_record['document_title']}\n"
                         f"Final Version: {archive_record['final_version']}\n"
                         f"Reviews: {archive_record['total_reviews']}\n"
                         f"Versions: {archive_record['total_versions']}\n"
                         f"Audit Entries: {archive_record['audit_trail_entries']}")
        
        shared["archive_record"] = archive_record
        self.add_audit_entry(shared, "document_archived", 
                           f"Archived document v{archive_record['final_version']}")
        
        # Show workflow summary
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        print(f"Document successfully processed through all stages.")
        print(f"Location: {archive_record['archive_location']}")
        
        return "completed"


# Sub-Flows
class WorkingGroupFlow(Flow):
    """Flow for working group document creation and approval."""
    
    def __init__(self):
        # Create nodes
        drafting = DocumentDraftingNode()
        peer_review = PeerReviewNode()
        version_control = VersionControlNode()
        wg_approval = WorkingGroupApprovalNode()
        
        # Set up flow
        drafting >> peer_review
        peer_review - "approved" >> version_control
        peer_review - "needs_revision" >> drafting
        peer_review - "rejected" >> drafting  # For major rework
        
        drafting - "revised" >> peer_review
        version_control >> wg_approval
        
        wg_approval - "needs_work" >> drafting
        
        super().__init__(start=drafting)
    
    def post(self, shared, prep_res, exec_res):
        # WorkingGroupFlow is complete when we get approval
        if exec_res == "approved":
            return "ready_for_committee"
        elif exec_res == "rejected":
            return "rejected_by_working_group"
        else:
            return exec_res


class CommitteeFlow(Flow):
    """Flow for committee review and approval."""
    
    def __init__(self):
        # Create nodes
        submission = SubmissionNode()
        committee_review = CommitteeReviewNode()
        clarification = ClarificationNode()
        committee_approval = CommitteeApprovalNode()
        
        # Set up flow
        submission >> committee_review
        committee_review - "approved" >> committee_approval
        committee_review - "clarification_needed" >> clarification
        committee_review - "rejected" >> committee_approval  # Still need formal rejection
        
        clarification >> committee_approval
        
        super().__init__(start=submission)
    
    def post(self, shared, prep_res, exec_res):
        # CommitteeFlow is complete when we get final decision
        if exec_res == "approved":
            return "approved_by_committee"
        else:
            return "rejected_by_committee"


# Main Document Workflow
class DocumentWorkflow(Flow):
    """Main document workflow orchestrating all phases."""
    
    def __init__(self, context_path: str = "context.yml"):
        # Create all nodes and flows
        context_loader = ContextLoaderNode()
        context_loader.set_params({"context_path": context_path})
        
        needs_assessment = NeedsAssessmentNode()
        outline_template = OutlineTemplateNode()
        role_assignment = RoleAssignmentNode()
        
        working_group = WorkingGroupFlow()
        committee = CommitteeFlow()
        
        publication = PublicationNode()
        training = TrainingImplementationNode()
        maintenance = MaintenanceReviewNode()
        archiving = ArchivingNode()
        
        # Set up main flow
        context_loader >> needs_assessment
        needs_assessment >> outline_template
        outline_template >> role_assignment
        role_assignment >> working_group
        
        working_group - "ready_for_committee" >> committee
        working_group - "rejected_by_working_group" >> archiving
        
        committee - "approved_by_committee" >> publication
        committee - "rejected_by_committee" >> archiving
        
        publication >> training
        training >> maintenance
        maintenance >> archiving
        
        super().__init__(start=context_loader)
    
    def post(self, shared, prep_res, exec_res):
        # Workflow is complete
        if exec_res == "completed":
            print("\n✅ Document workflow completed successfully!")
            return "success"
        else:
            return exec_res


# Example Usage
def main():
    """Run the document workflow with example context."""
    print("Document Approval Workflow Demo")
    print("==============================\n")
    
    # Check if context file exists
    context_path = Path("context.yml")
    if not context_path.exists():
        print("❌ Error: context.yml not found!")
        print("Please ensure context.yml exists in the current directory.")
        return
    
    # Initialize shared state
    shared_state = {
        "workflow_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "start_time": datetime.datetime.now().isoformat()
    }
    
    # Create and run workflow
    workflow = DocumentWorkflow(str(context_path))
    result = workflow.run(shared_state)
    
    # Show final statistics
    print("\n" + "="*60)
    print("Workflow Statistics")
    print("="*60)
    print(f"Workflow ID: {shared_state['workflow_id']}")
    print(f"Start Time: {shared_state['start_time']}")
    print(f"End Time: {datetime.datetime.now().isoformat()}")
    print(f"Total Audit Entries: {len(shared_state.get('audit_trail', []))}")
    print(f"Total Reviews: {len(shared_state.get('reviews', []))}")
    print(f"Total Approvals: {len(shared_state.get('approvals', []))}")
    print(f"Final Status: {result}")
    
    # Optionally save audit trail
    save_audit = input("\nSave audit trail to file? (y/n): ")
    if save_audit.lower() == 'y':
        audit_filename = f"audit_trail_{shared_state['workflow_id']}.json"
        with open(audit_filename, 'w') as f:
            json.dump({
                "workflow_id": shared_state["workflow_id"],
                "audit_trail": shared_state.get("audit_trail", []),
                "reviews": shared_state.get("reviews", []),
                "approvals": shared_state.get("approvals", [])
            }, f, indent=2)
        print(f"✓ Audit trail saved to: {audit_filename}")


if __name__ == "__main__":
    main()