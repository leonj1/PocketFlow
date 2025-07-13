import asyncio
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
            - Extract `things_to_remove` (What is mandatory that should be removed from the document).
            - Extract `things_to_add` (What is mandatory that should be added to the document).
            - Extract `things_to_change` (What is mandatory that should be changed in the document).

            **Example Format:**
            ```yaml
            approval: in_favor
            things_to_remove: "Remove this and that"
            things_to_add: "Add this and that"
            things_to_change: "Change this and that"
            ```

            Generate the YAML output now:
        """
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        return response

    async def post_async(self, shared, prep_res, exec_res):
        print(f"\n {self.review_name} Completed!")
        if exec_res and isinstance(exec_res, dict):
            shared["feedback"]["things_to_remove"].append(exec_res.get("things_to_remove", ""))
            shared["feedback"]["things_to_add"].append(exec_res.get("things_to_add", ""))
            shared["feedback"]["things_to_change"].append(exec_res.get("things_to_change", ""))
            return exec_res.get("approval", "abstain")
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
        await asyncio.gather(
            app_security_flow.run_async(shared),
            cloud_flow.run_async(shared),
            network_engineering_flow.run_async(shared),
            software_architect_flow.run_async(shared),
            chief_technology_officer_flow.run_async(shared),
            product_manager_flow.run_async(shared)
        )
        print("\n Committee Review Completed!")
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