import asyncio
from pocketflow import Node, Flow, AsyncNode, AsyncFlow
from utils import call_llm, call_llm_thinking

class AsyncAppSecurityReview(AsyncNode):
    async def prep_async(self, shared):
        pass

    async def exec_async(self, inputs):
        pass

    async def post_async(self, shared, prep_res, exec_res):
        print("\n App Security Review")
        pass

class AsyncCloudReview(AsyncNode):
    async def prep_async(self, shared):
        pass

    async def exec_async(self, inputs):
        pass

    async def post_async(self, shared, prep_res, exec_res):
        print("\n Cloud Review")
        pass

class AsyncNetworkEngineeringReview(AsyncNode):
    async def prep_async(self, shared):
        pass

    async def exec_async(self, inputs):
        pass

    async def post_async(self, shared, prep_res, exec_res):
        print("\n Network Engineering Review")
        pass

class AsyncSoftwareSrchitectReview(AsyncNode):
    async def prep_async(self, shared):
        pass

    async def exec_async(self, inputs):
        pass

    async def post_async(self, shared, prep_res, exec_res):
        print("\n Software Architect Review")
        pass

class AsyncChiefTechnologyOfficerReview(AsyncNode):
    async def prep_async(self, shared):
        pass

    async def exec_async(self, inputs):
        pass

    async def post_async(self, shared, prep_res, exec_res):
        print("\n Chief Technology Officer Review")
        pass

class AsyncProductManagerReview(AsyncNode):
    async def prep_async(self, shared):
        pass

    async def exec_async(self, inputs):
        pass

    async def post_async(self, shared, prep_res, exec_res):
        print("\n Product Manager Review")
        pass

# Create nodes
app_security_review = AsyncAppSecurityReview()
cloud_review = AsyncCloudReview()
network_engineering_review = AsyncNetworkEngineeringReview()
software_architect_review = AsyncSoftwareSrchitectReview()
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
