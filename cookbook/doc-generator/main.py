# from flows import flow
from pocketflow import Node, Flow
from flows.working_group import working_group_flow
from flows.comittee import app_security_flow, cloud_flow, network_engineering_flow, software_architect_flow, chief_technology_officer_flow, product_manager_flow, committee_flow
from flows.working_group import group_evaluator_node, group_lead_node
from flows.comittee import committee_node

class EndNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nDocument Generator ended!")
        pass

class AbandonNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nAbandoning document creation")
        pass

class PublisherNode(Node):
    def post(self, shared, prep_res, exec_res):
        print("\nWriting the document")
        pass

def main():
    print("\nWelcome to Document Generator!")
    print("=========================")
    
    # Initialize shared store
    with open("/app/cookbook/doc-generator/context.yml", "r") as f:
        context = f.read()
    shared = {
        "context": context,
        "next_step": "start",
        "document": "",
        "attempts": {
            "current": 0,
            "max": 3
        },
        "feedback": {
            "things_to_remove": "",
            "things_to_add": "",
            "things_to_change": ""
        },
        "approvals": {
            "in_favor": 0,
            "against": 0,
            "abstain": 0
        }
    }

    # Create flows
    abandon_node = AbandonNode()
    end_node = EndNode()
    publisher_node = PublisherNode()
    
    # connect nodes
    group_evaluator_node - "ready_for_committee" >> committee_node
    group_lead_node - "abandon" >> abandon_node
    committee_node - "approved_by_committee" >> publisher_node
    committee_node - "rejected_by_committee" >> group_lead_node

    # Run the flow
    working_group_flow.run(shared)
    
    print("\nDocument Generator completed!")

if __name__ == "__main__":
    main() 
