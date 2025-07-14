import asyncio
import yaml
import re
from pocketflow import Node, Flow, AsyncNode, AsyncFlow
from utils import call_llm, call_llm_thinking

class AsyncSectionReviewNode(AsyncNode):
    """Base class for committee members reviewing specific sections"""
    
    def __init__(self, review_name, personality, focus_sections=None):
        super().__init__()
        self.review_name = review_name
        self.personality = personality
        self.focus_sections = focus_sections or []  # Sections this reviewer should focus on
    
    async def prep_async(self, shared):
        print(f"\n {self.review_name} - Section Review")
        
        # Check if we have sections to review
        if "sections" not in shared:
            return None
            
        # Get sections this reviewer should focus on
        sections_to_review = {}
        for section_name, section_data in shared["sections"].items():
            # Skip if section not completed
            if section_data["status"] != "completed":
                continue
                
            # Check if this reviewer should review this section
            if self.focus_sections:
                # If specific focus sections defined, only review those
                if section_name in self.focus_sections:
                    sections_to_review[section_name] = section_data
            else:
                # Otherwise review sections that match reviewer's expertise
                audience = section_data.get("audience_focus", ["All"])
                if "All" in audience or any(role in self.personality for role in audience):
                    sections_to_review[section_name] = section_data
        
        if not sections_to_review:
            return None
            
        return {
            "sections_to_review": sections_to_review,
            "context": shared["context"],
            "full_document": shared.get("document", "")
        }
    
    def parse_yaml_response(self, response_text):
        """Extract and parse YAML from the LLM response."""
        try:
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response_text, re.DOTALL)
            if yaml_match:
                yaml_text = yaml_match.group(1)
            else:
                yaml_text = response_text
            
            parsed = yaml.safe_load(yaml_text)
            
            # Handle both overall and section-specific feedback
            if "sections" in parsed:
                # Section-specific format
                return parsed
            else:
                # Overall document format (backward compatibility)
                return {
                    "overall_approval": parsed.get("approval", "abstain"),
                    "overall_feedback": {
                        "things_to_remove": parsed.get("things_to_remove", ""),
                        "things_to_add": parsed.get("things_to_add", ""),
                        "things_to_change": parsed.get("things_to_change", "")
                    }
                }
                
        except Exception as e:
            print(f"Error parsing YAML response: {e}")
            return {
                "overall_approval": "abstain",
                "overall_feedback": {
                    "things_to_remove": "",
                    "things_to_add": "",
                    "things_to_change": ""
                }
            }
    
    async def exec_async(self, prep_data):
        if not prep_data:
            return None
            
        sections_to_review = prep_data["sections_to_review"]
        context = prep_data["context"]
        
        # Build section-focused prompt
        prompt = f"""
        {self.personality}
        
        Review the following sections of a document about: {context['topic']}
        
        Document Purpose: {context['purpose']}
        
        Sections to Review:
        """
        
        for section_name, section_data in sections_to_review.items():
            prompt += f"\n\n### {section_name}\n"
            prompt += f"Target Audience: {', '.join(section_data.get('audience_focus', ['All']))}\n"
            prompt += f"Content:\n{section_data['content']}\n"
        
        prompt += """
        
        Provide feedback in YAML format for each section AND overall:
        ```yaml
        overall_approval: "in_favor" or "against" or "abstain"
        sections:
          Section Name 1:
            approval: "in_favor" or "against" or "abstain"
            quality_score: [1-10]
            things_to_remove: "specific content to remove"
            things_to_add: "specific content to add"
            things_to_change: "specific changes needed"
          Section Name 2:
            approval: "in_favor" or "against" or "abstain"
            quality_score: [1-10]
            things_to_remove: "specific content to remove"
            things_to_add: "specific content to add"
            things_to_change: "specific changes needed"
        ```
        
        Consider:
        1. Technical accuracy for your area of expertise
        2. Completeness for the target audience
        3. Clarity and coherence
        4. Compliance with requirements
        5. Security implications (if applicable)
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        print(f"\n {self.review_name} Response: {response[:200]}...")
        
        parsed_response = self.parse_yaml_response(response)
        return parsed_response
    
    async def post_async(self, shared, prep_res, exec_res):
        print(f"\n {self.review_name} Section Review Completed!")
        
        if exec_res and isinstance(exec_res, dict):
            # Process section-specific feedback
            if "sections" in exec_res:
                for section_name, feedback in exec_res["sections"].items():
                    if section_name in shared["sections"]:
                        section_data = shared["sections"][section_name]
                        
                        # Update section-specific feedback
                        if feedback.get("things_to_remove"):
                            section_data["feedback"]["things_to_remove"].append(
                                f"[{self.review_name}] {feedback['things_to_remove']}"
                            )
                        if feedback.get("things_to_add"):
                            section_data["feedback"]["things_to_add"].append(
                                f"[{self.review_name}] {feedback['things_to_add']}"
                            )
                        if feedback.get("things_to_change"):
                            section_data["feedback"]["things_to_change"].append(
                                f"[{self.review_name}] {feedback['things_to_change']}"
                            )
                        
                        # Track reviewer scores
                        if "reviewer_scores" not in section_data:
                            section_data["reviewer_scores"] = {}
                        section_data["reviewer_scores"][self.review_name] = {
                            "quality_score": feedback.get("quality_score", 7),
                            "approval": feedback.get("approval", "abstain")
                        }
                        
                        print(f"  - {section_name}: {feedback.get('approval', 'abstain')} "
                              f"(Quality: {feedback.get('quality_score', 'N/A')}/10)")
            
            # Handle overall approval
            overall_approval = exec_res.get("overall_approval", "abstain")
            
            # Visual indicators
            if overall_approval == "in_favor":
                icon = "✅"
            elif overall_approval == "against":
                icon = "❌"
            else:
                icon = "⚪"
            
            print(f"{self.review_name} overall verdict: {icon} {overall_approval}")
            return overall_approval
        
        print(f"{self.review_name} outcome: ⚪ abstain")
        return "abstain"

# Specialized section reviewers
class AsyncSecuritySectionReview(AsyncSectionReviewNode):
    def __init__(self):
        super().__init__(
            "Security Section Expert",
            "You are a security engineer focusing on authentication and authorization sections.",
            focus_sections=["Authentication Guidelines", "Authorization Patterns", "Security Checklist"]
        )

class AsyncArchitectureSectionReview(AsyncSectionReviewNode):
    def __init__(self):
        super().__init__(
            "Architecture Section Expert",
            "You are a software architect focusing on design patterns and implementation.",
            focus_sections=["Core Security Principles", "Implementation Examples", "Appendices"]
        )

class AsyncProductSectionReview(AsyncSectionReviewNode):
    def __init__(self):
        super().__init__(
            "Product Section Expert",
            "You are a product manager focusing on user experience and adoption.",
            focus_sections=["Executive Summary", "Implementation Examples", "Security Checklist"]
        )

# Create section-aware committee flow
class AsyncSectionCommitteeFlow(AsyncFlow):
    async def run_async(self, shared):
        print("\n Section-Aware Committee Review Starting...")
        
        # Create section-specific reviewers
        security_reviewer = AsyncSecuritySectionReview()
        architecture_reviewer = AsyncArchitectureSectionReview()
        product_reviewer = AsyncProductSectionReview()
        
        # Also keep general reviewers from original committee
        from flows.comittee import (
            app_security_review,
            cloud_review,
            network_engineering_review,
            chief_technology_officer_review
        )
        
        # Run all reviews in parallel
        review_tasks = [
            security_reviewer.prep_async(shared).then(
                lambda p: security_reviewer.exec_async(p) if p else None
            ).then(
                lambda e: security_reviewer.post_async(shared, None, e) if e else "abstain"
            ),
            architecture_reviewer.prep_async(shared).then(
                lambda p: architecture_reviewer.exec_async(p) if p else None
            ).then(
                lambda e: architecture_reviewer.post_async(shared, None, e) if e else "abstain"
            ),
            product_reviewer.prep_async(shared).then(
                lambda p: product_reviewer.exec_async(p) if p else None
            ).then(
                lambda e: product_reviewer.post_async(shared, None, e) if e else "abstain"
            ),
        ]
        
        # Execute all reviews
        outcomes = []
        for task in review_tasks:
            try:
                # Simple sequential execution since we can't use .then()
                reviewer = task
                if isinstance(task, AsyncSecuritySectionReview):
                    reviewer = security_reviewer
                elif isinstance(task, AsyncArchitectureSectionReview):
                    reviewer = architecture_reviewer
                elif isinstance(task, AsyncProductSectionReview):
                    reviewer = product_reviewer
                
                prep_res = await reviewer.prep_async(shared)
                exec_res = await reviewer.exec_async(prep_res) if prep_res else None
                outcome = await reviewer.post_async(shared, prep_res, exec_res) if exec_res else "abstain"
                outcomes.append(outcome)
            except Exception as e:
                print(f"Review error: {e}")
                outcomes.append("abstain")
        
        # Also run general committee reviews
        general_outcomes = await asyncio.gather(
            self._run_general_review(app_security_review, shared),
            self._run_general_review(cloud_review, shared),
            self._run_general_review(network_engineering_review, shared),
            self._run_general_review(chief_technology_officer_review, shared)
        )
        
        outcomes.extend(general_outcomes)
        
        # Count votes
        in_favor_count = outcomes.count("in_favor")
        against_count = outcomes.count("against")
        abstain_count = outcomes.count("abstain")
        
        # Update shared approval counts
        shared["approvals"]["in_favor"] = in_favor_count
        shared["approvals"]["against"] = against_count
        shared["approvals"]["abstain"] = abstain_count
        
        print("\n Section-Aware Committee Review Completed!")
        print(f"Votes - In Favor: {in_favor_count}, Against: {against_count}, Abstain: {abstain_count}")
        
        # Analyze section-specific feedback
        if "sections" in shared:
            print("\nSection-Specific Summary:")
            for section_name, section_data in shared["sections"].items():
                if "reviewer_scores" in section_data:
                    avg_score = sum(r["quality_score"] for r in section_data["reviewer_scores"].values()) / len(section_data["reviewer_scores"])
                    print(f"  - {section_name}: Average Quality {avg_score:.1f}/10")
        
        # Determine outcome
        if against_count > 0:
            return "rejected_by_committee"
        elif in_favor_count == 0:
            return "rejected_by_committee"
        elif in_favor_count > abstain_count:
            return "approved_by_committee"
        else:
            return "rejected_by_committee"
    
    async def _run_general_review(self, reviewer, shared):
        """Run a general reviewer on the full document"""
        try:
            prep_res = await reviewer.prep_async(shared)
            exec_res = await reviewer.exec_async(prep_res) if prep_res else None
            outcome = await reviewer.post_async(shared, prep_res, exec_res) if exec_res else "abstain"
            return outcome
        except Exception as e:
            print(f"General review error: {e}")
            return "abstain"

# Create synchronous wrapper for the section committee
class SectionCommitteeNode(Node):
    def __init__(self):
        super().__init__()
        self.async_flow = AsyncSectionCommitteeFlow(start=None)
    
    def post(self, shared, prep_res, exec_res):
        result = asyncio.run(self.async_flow.run_async(shared))
        return result

# Export the nodes and flows
section_committee_node = SectionCommitteeNode()
section_committee_flow = Flow(start=section_committee_node)