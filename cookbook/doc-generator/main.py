# from flows import flow
import yaml
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
    def prep(self, shared):
        print("\n Publisher Node")
        return {
            "document": shared["document"],
            "output_filename": shared["context"]["output_filename"]
        }

    def exec(self, prep_res):
        # save the document to a file
        with open(prep_res["output_filename"], "w") as f:
            f.write(prep_res["document"])

        return None

    def post(self, shared, prep_res, exec_res):
        print(f"\n Publisher Node Completed. Result: {exec_res}")
        return None

class ComitteeEvaluatorNode(Node):
    def prep(self, shared):
        print("\n Comittee Evaluation Node")
        return shared["approvals"]

    def exec(self, approvals):
        # if approval against is greater than 0 then reject
        if approvals["against"] > 0:
            return "rejected_by_committee"
        if approvals["in_favor"] == 0:
            return "rejected_by_committee"
        # if in favor count is greater than abstain
        if approvals["in_favor"] > approvals["abstain"]:
            return "approved_by_committee"

        return "rejected_by_committee"

    def post(self, shared, prep_res, exec_res):
        print(f"\n Comittee Evaluation Node Completed. Result: {exec_res}")
        return exec_res

def main():
    print("\nWelcome to Document Generator!")
    print("=========================")
    
    # Initialize shared store
    with open("/app/cookbook/doc-generator/context.yml", "r") as f:
        context = yaml.safe_load(f)
    shared = {
        "context": context,
        "next_step": "start",
        "document": {
            "title": "",
            "sections": []
        },
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
