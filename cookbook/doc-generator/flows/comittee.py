import asyncio
import yaml
import re
from pocketflow import Node, Flow, AsyncNode, AsyncFlow
from utils import call_llm, call_llm_thinking

class AsyncReviewNode(AsyncNode):
    """Base class for all review nodes with common functionality"""
    
    def __init__(self, review_name, personality):
        super().__init__()
        self.review_name = review_name
        self.personality = personality
    
    async def prep_async(self, shared):
        print(f"\n {self.review_name}")
        # if document is not in shared, return None
        if "document" not in shared:
            return None
        return shared["document"]

    def parse_yaml_response(self, response_text):
        """Extract and parse YAML from the LLM response."""
        try:
            # Try to find YAML between ```yaml and ``` markers
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response_text, re.DOTALL)
            if yaml_match:
                yaml_text = yaml_match.group(1)
            else:
                # If no markers, try to parse the whole response as YAML
                yaml_text = response_text
            
            # Parse the YAML
            parsed = yaml.safe_load(yaml_text)
            
            # Ensure all required fields exist with defaults
            result = {
                "approval": parsed.get("approval", "abstain"),
                "things_to_remove": parsed.get("things_to_remove", ""),
                "things_to_add": parsed.get("things_to_add", ""),
                "things_to_change": parsed.get("things_to_change", "")
            }
            
            return result
        except Exception as e:
            print(f"Error parsing YAML response: {e}")
            # Return default values if parsing fails
            return {
                "approval": "abstain",
                "things_to_remove": "",
                "things_to_add": "",
                "things_to_change": ""
            }

    async def exec_async(self, document):
        if document is None:
            return None

        # Call LLM with the entire conversation history
        prompt = f"""
            {self.personality}
            Draft a document based on the following context:
            <document>{document}</document>
            **YAML Output Requirements:**
            - Extract `approval` (`in_favor`, `against`, or `abstain`).
            - Extract `things_to_remove` (What is mandatory that should be removed from the document. Only include content if you have specific recommendations. Leave blank if no removals are needed.).
            - Extract `things_to_add` (What is mandatory that should be added to the document. Only include content if you have specific recommendations. Leave blank if no additions are needed.).
            - Extract `things_to_change` (What is mandatory that should be changed in the document. Only include content if you have specific recommendations. Leave blank if no changes are needed.).

            **Important Instructions:**
            - Only populate `things_to_remove`, `things_to_add`, and `things_to_change` when you have actual, specific recommendations.
            - If you have no recommendations for a field, leave it completely empty (blank string).
            - Do NOT include explanatory text like "nothing to remove" or "no changes needed".

            **Example Format:**
            ```yaml
            approval: abstain
            things_to_remove: "Remove this specific section"
            things_to_add: "Add this specific requirement"
            things_to_change: ""
            Generate the YAML output now:
        """

        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        print(f"\n {self.review_name} Completed! Response: {response}")
        
        # Parse the YAML response
        parsed_response = self.parse_yaml_response(response)
        return parsed_response

    async def post_async(self, shared, prep_res, exec_res):
        print(f"\n {self.review_name} Completed!")
        if exec_res and isinstance(exec_res, dict):
            shared["feedback"]["things_to_remove"].append(exec_res.get("things_to_remove", ""))
            shared["feedback"]["things_to_add"].append(exec_res.get("things_to_add", ""))
            shared["feedback"]["things_to_change"].append(exec_res.get("things_to_change", ""))
            outcome = exec_res.get("approval", "abstain")
            # Add visual indicators for different outcomes
            if outcome == "in_favor":
                icon = "✅"
            elif outcome == "against":
                icon = "❌"
            else:  # abstain
                icon = "⚪"
            print(f"Committee {self.review_name} outcome: {icon} {outcome}")
            return outcome
        print(f"Committee {self.review_name} outcome: ⚪ abstain")
        return "abstain"

class AsyncAppSecurityReview(AsyncReviewNode):
    def __init__(self):
        super().__init__(
            "App Security Review",
            "You are a security engineer with 10 years of experience in application security."
        )

class AsyncCloudReview(AsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Cloud Review",
            "You are a cloud engineer with 10 years of experience in cloud security."
        )

class AsyncNetworkEngineeringReview(AsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Network Engineering Review",
            "You are a network engineer with 10 years of experience in network security and architecture."
        )

class AsyncSoftwareArchitectReview(AsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Software Architect Review",
            "You are a software architect with 10 years of experience in system design and architecture."
        )

class AsyncChiefTechnologyOfficerReview(AsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Chief Technology Officer Review",
            "You are a Chief Technology Officer with 15 years of experience in technology leadership and strategy."
        )

class AsyncProductManagerReview(AsyncReviewNode):
    def __init__(self):
        super().__init__(
            "Product Manager Review",
            "You are a product manager with 10 years of experience in product development and strategy."
        )

# Create nodes
app_security_review = AsyncAppSecurityReview()
cloud_review = AsyncCloudReview()
network_engineering_review = AsyncNetworkEngineeringReview()
software_architect_review = AsyncSoftwareArchitectReview()
chief_technology_officer_review = AsyncChiefTechnologyOfficerReview()
product_manager_review = AsyncProductManagerReview()

# Create flows
app_security_flow = AsyncFlow(start=app_security_review)
cloud_flow = AsyncFlow(start=cloud_review)
network_engineering_flow = AsyncFlow(start=network_engineering_review)
software_architect_flow = AsyncFlow(start=software_architect_review)
chief_technology_officer_flow = AsyncFlow(start=chief_technology_officer_review)
product_manager_flow = AsyncFlow(start=product_manager_review)

# Create committee flow that runs all reviews in parallel
class AsyncCommitteeFlow(AsyncFlow):
    async def run_async(self, shared):
        print("\n Committee Review Starting...")
        # Run all reviews in parallel and collect outcomes
        outcomes = await asyncio.gather(
            app_security_flow.run_async(shared),
            cloud_flow.run_async(shared),
            network_engineering_flow.run_async(shared),
            software_architect_flow.run_async(shared),
            chief_technology_officer_flow.run_async(shared),
            product_manager_flow.run_async(shared)
        )
        
        # Count the votes
        in_favor_count = outcomes.count("in_favor")
        against_count = outcomes.count("against")
        abstain_count = outcomes.count("abstain")
        
        # Update shared approval counts
        shared["approvals"]["in_favor"] = in_favor_count
        shared["approvals"]["against"] = against_count
        shared["approvals"]["abstain"] = abstain_count
        
        print("\n Committee Review Completed!")
        print(f"Votes - In Favor: {in_favor_count}, Against: {against_count}, Abstain: {abstain_count}")
        
        # Evaluate committee decision based on feedback
        has_feedback = False
        
        # Check if any agent provided feedback to change the document
        for feedback_type in ["things_to_remove", "things_to_add", "things_to_change"]:
            for feedback in shared["feedback"][feedback_type]:
                if feedback and feedback.strip():  # Check if feedback is not empty
                    has_feedback = True
                    break
            if has_feedback:
                break
        
        if has_feedback:
            print(f"Rejected by committee because agents provided feedback for changes")
            return "rejected_by_committee"
        else:
            print(f"Approved by committee because no agents requested changes")
            return "approved_by_committee"

# Create a synchronous wrapper node for the async committee flow
class CommitteeNode(Node):
    def __init__(self):
        super().__init__()
        self.async_flow = AsyncCommitteeFlow(start=app_security_review)
    
    def post(self, shared, prep_res, exec_res):
        # Run the async flow synchronously
        result = asyncio.run(self.async_flow.run_async(shared))
        return result

# Create the committee flow as a synchronous flow
committee_node = CommitteeNode()
committee_flow = Flow(start=committee_node)
