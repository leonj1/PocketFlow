import asyncio
import yaml
import re
from pocketflow import Node, Flow, AsyncNode, AsyncFlow
from utils import call_llm, call_llm_thinking
import json

# Import original committee nodes
from comittee import AsyncReviewNode

class EnhancedAsyncReviewNode(AsyncReviewNode):
    """Enhanced review node that considers completeness analysis"""
    
    async def prep_async(self, shared):
        print(f"\n Enhanced {self.review_name}")
        
        # Check for document
        if "document" not in shared:
            return None
        
        # Prepare review context with completeness analysis
        review_context = {
            "document": shared["document"],
            "completeness_analysis": shared.get("completeness_analysis", None),
            "completeness_score": None,
            "critical_issues": []
        }
        
        # Extract key completeness insights
        if review_context["completeness_analysis"]:
            analysis = review_context["completeness_analysis"]
            review_context["completeness_score"] = analysis.get("overall_completeness", "N/A")
            
            # Collect critical issues relevant to this reviewer
            if "Security" in self.personality and analysis.get("unfulfilled_goals"):
                security_goals = [g for g in analysis["unfulfilled_goals"] 
                                if any(term in g.get("goal", "").lower() 
                                     for term in ["security", "authentication", "authorization"])]
                if security_goals:
                    review_context["critical_issues"].extend(security_goals)
            
            if "Architecture" in self.personality and analysis.get("conceptual_gaps"):
                review_context["critical_issues"].extend(analysis["conceptual_gaps"])
            
            if "Product" in self.personality and analysis.get("readability_issues"):
                review_context["critical_issues"].extend(analysis["readability_issues"])
        
        return review_context
    
    async def exec_async(self, prep_data):
        if not prep_data:
            return None
        
        document = prep_data["document"]
        completeness_score = prep_data["completeness_score"]
        critical_issues = prep_data["critical_issues"]
        
        # Build enhanced prompt with completeness context
        prompt = f"""
        {self.personality}
        
        Review the following document with awareness of its completeness analysis:
        
        Completeness Score: {completeness_score}/100
        
        Critical Issues Relevant to Your Expertise:
        {json.dumps(critical_issues, indent=2) if critical_issues else "None identified"}
        
        <document>{document}</document>
        
        Consider the completeness analysis in your review. If the document has:
        - Low completeness score (< 70): Be more critical
        - Unfulfilled goals: Check if your area addresses them
        - Conceptual gaps: Verify technical coherence
        - Readability issues: Consider audience impact
        
        **YAML Output Requirements:**
        - Extract `approval` (`in_favor`, `against`, or `abstain`).
        - Extract `things_to_remove` (What must be removed).
        - Extract `things_to_add` (What must be added, including completeness gaps).
        - Extract `things_to_change` (What must be changed).
        - Include `completeness_concerns` (Specific completeness issues in your domain).
        
        **Example Format:**
        ```yaml
        approval: in_favor
        things_to_remove: "Remove redundant sections"
        things_to_add: "Add missing authentication details"
        things_to_change: "Simplify technical jargon"
        completeness_concerns: "Security goals not fully addressed"
        ```
        
        Generate the YAML output now:
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        print(f"\n Enhanced {self.review_name} Response: {response[:200]}...")
        
        # Parse the enhanced YAML response
        parsed_response = self.parse_enhanced_yaml(response)
        return parsed_response
    
    def parse_enhanced_yaml(self, response_text):
        """Parse YAML with completeness fields"""
        try:
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response_text, re.DOTALL)
            if yaml_match:
                yaml_text = yaml_match.group(1)
            else:
                yaml_text = response_text
            
            parsed = yaml.safe_load(yaml_text)
            
            result = {
                "approval": parsed.get("approval", "abstain"),
                "things_to_remove": parsed.get("things_to_remove", ""),
                "things_to_add": parsed.get("things_to_add", ""),
                "things_to_change": parsed.get("things_to_change", ""),
                "completeness_concerns": parsed.get("completeness_concerns", "")
            }
            
            return result
        except Exception as e:
            print(f"Error parsing enhanced YAML response: {e}")
            return {
                "approval": "abstain",
                "things_to_remove": "",
                "things_to_add": "",
                "things_to_change": "",
                "completeness_concerns": ""
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        print(f"\n Enhanced {self.review_name} Completed!")
        
        if exec_res and isinstance(exec_res, dict):
            # Process standard feedback
            shared["feedback"]["things_to_remove"].append(exec_res.get("things_to_remove", ""))
            shared["feedback"]["things_to_add"].append(exec_res.get("things_to_add", ""))
            shared["feedback"]["things_to_change"].append(exec_res.get("things_to_change", ""))
            
            # Track completeness concerns
            if exec_res.get("completeness_concerns"):
                if "completeness_concerns_by_reviewer" not in shared:
                    shared["completeness_concerns_by_reviewer"] = {}
                shared["completeness_concerns_by_reviewer"][self.review_name] = exec_res["completeness_concerns"]
            
            outcome = exec_res.get("approval", "abstain")
            
            # Adjust approval based on completeness
            if prep_res and prep_res.get("completeness_score", 100) < 70 and outcome == "in_favor":
                print(f"  Warning: {self.review_name} approved despite low completeness score")
            
            # Visual indicators
            if outcome == "in_favor":
                icon = "✅"
            elif outcome == "against":
                icon = "❌"
            else:
                icon = "⚪"
            
            print(f"Enhanced Committee {self.review_name} outcome: {icon} {outcome}")
            return outcome
        
        print(f"Enhanced Committee {self.review_name} outcome: ⚪ abstain")
        return "abstain"

# Create enhanced review nodes
class EnhancedAppSecurityReview(EnhancedAsyncReviewNode):
    def __init__(self):
        super().__init__(
            "App Security Review",
            "You are a security engineer with 10 years of experience in application security."
        )

class EnhancedCloudReview(EnhancedAsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Cloud Review",
            "You are a cloud engineer with 10 years of experience in cloud security."
        )

class EnhancedNetworkEngineeringReview(EnhancedAsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Network Engineering Review",
            "You are a network engineer with 10 years of experience in network security and architecture."
        )

class EnhancedSoftwareArchitectReview(EnhancedAsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Software Architect Review",
            "You are a software architect with 10 years of experience in system design and architecture."
        )

class EnhancedChiefTechnologyOfficerReview(EnhancedAsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Chief Technology Officer Review",
            "You are a Chief Technology Officer with 15 years of experience in technology leadership and strategy."
        )

class EnhancedProductManagerReview(EnhancedAsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Product Manager Review",
            "You are a product manager with 10 years of experience in product development and strategy."
        )

# Create enhanced committee flow
class EnhancedAsyncCommitteeFlow(AsyncFlow):
    async def run_async(self, shared):
        print("\n Enhanced Committee Review Starting...")
        
        # Create enhanced review nodes
        enhanced_reviews = [
            EnhancedAppSecurityReview(),
            EnhancedCloudReview(),
            EnhancedNetworkEngineeringReview(),
            EnhancedSoftwareArchitectReview(),
            EnhancedChiefTechnologyOfficerReview(),
            EnhancedProductManagerReview()
        ]
        
        # Run all reviews in parallel
        outcomes = []
        for reviewer in enhanced_reviews:
            prep_res = await reviewer.prep_async(shared)
            exec_res = await reviewer.exec_async(prep_res) if prep_res else None
            outcome = await reviewer.post_async(shared, prep_res, exec_res) if exec_res else "abstain"
            outcomes.append(outcome)
        
        # Count votes
        in_favor_count = outcomes.count("in_favor")
        against_count = outcomes.count("against")
        abstain_count = outcomes.count("abstain")
        
        # Update shared approval counts
        shared["approvals"]["in_favor"] = in_favor_count
        shared["approvals"]["against"] = against_count
        shared["approvals"]["abstain"] = abstain_count
        
        print("\n Enhanced Committee Review Completed!")
        print(f"Votes - In Favor: {in_favor_count}, Against: {against_count}, Abstain: {abstain_count}")
        
        # Display completeness concerns if any
        if "completeness_concerns_by_reviewer" in shared:
            print("\nCompleteness Concerns by Reviewer:")
            for reviewer, concern in shared["completeness_concerns_by_reviewer"].items():
                if concern:
                    print(f"  - {reviewer}: {concern}")
        
        # Decision logic with completeness consideration
        completeness_score = shared.get("completeness_analysis", {}).get("overall_completeness", 100)
        print(f"  Document Completeness: {completeness_score}/100")
        
        if against_count > 0:
            return "rejected_by_committee"
        elif completeness_score < 50 and in_favor_count < 4:
            # Require super-majority for very incomplete documents
            print("  Document rejected due to low completeness and insufficient support")
            return "rejected_by_committee"
        elif in_favor_count == 0:
            print("  Document rejected due to no committee member approving")
            return "rejected_by_committee"
        elif in_favor_count > abstain_count:
            print("  Document approved by committee since super-majority approved")
            return "approved_by_committee"
        else:
            print("  Document rejected by committee since super-majority did not approve")
            return "rejected_by_committee"

# Create synchronous wrapper for enhanced committee
class EnhancedCommitteeNode(Node):
    def __init__(self):
        super().__init__()
        self.async_flow = EnhancedAsyncCommitteeFlow(start=None)
    
    def post(self, shared, prep_res, exec_res):
        # Run the enhanced async flow
        result = asyncio.run(self.async_flow.run_async(shared))
        return result

# Export enhanced nodes and flows
enhanced_committee_node = EnhancedCommitteeNode()
enhanced_committee_flow = Flow(start=enhanced_committee_node)