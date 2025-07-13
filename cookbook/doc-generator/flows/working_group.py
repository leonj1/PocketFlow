from pocketflow import Node, Flow
import sys
sys.path.append('/app/cookbook/doc-generator')
from utils import call_llm, call_llm_thinking
import yaml

class GroupLeadNode(Node):
    """ Group Lead Node purpose is to determine whether to abandon iterating over the document. """

    def prep(self, shared):
        print("\n Group Lead Node")
        # if number of attempts reached max, abandon
        if shared["attempts"]["current"] >= shared["attempts"]["max"]:
            return "abandon"
        return shared["context"]

    def post(self, shared, prep_res, exec_res):
        if prep_res == 'abandon':
            return "abandon"  # End the conversation
        return None

class DocumentDraftingNode(Node):
    def prep(self, shared):
        print("\n Document Drafting Node")
        return shared["context"]

    def exec(self, context):
        if context is None:
            return None

        # context is already a parsed dictionary
        document_structure = context["deliverables"][0]["sections"]

        # Call LLM with the entire conversation history
        writing_style = "Write the documents adhering to the writing style of Elements of Style."
        prompt = f"""
            Draft a document based on the following context:
            <context>{context}</context>
            <document_structure>{document_structure}</document_structure>
            <style>{writing_style}</style>
        """
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        return response

    def post(self, shared, prep_res, exec_res):
        # count the number of words in exec_res
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n Document Drafting Node Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print("\n Document Drafting Node Skipped - No response generated")
        return None

class FeedbackNode(Node):
    """Base class for feedback nodes that modify documents based on feedback."""
    
    def __init__(self, feedback_type, action_verb):
        self.feedback_type = feedback_type
        self.action_verb = action_verb
        self.node_name = f"Things To {feedback_type.title()} Node"
        super().__init__()
    
    def prep(self, shared):
        print(f"\n {self.node_name}")
        feedback_list = shared["feedback"][f"things_to_{self.feedback_type}"]
        # Check if the feedback list is empty or contains only empty strings
        if not feedback_list or all(item == "" for item in feedback_list):
            return None

        # Join all non-empty feedback items
        feedback_text = "\n".join([item for item in feedback_list if item])

        # context is already a parsed dictionary from shared
        context_dict = shared["context"]
        document_structure = context_dict["deliverables"][0]["sections"]
        
        return {
            "document": shared["document"], 
            f"things_to_{self.feedback_type}": feedback_text,
            "document_structure": document_structure
        }

    def exec(self, context):
        if context is None:
            return None
        
        writing_style = "Write the documents adhering to the writing style of Elements of Style."
        prompt = f"""
            Ensure the document adheres to the following structure:
            <document_structure>{context["document_structure"]}</document_structure>
            Clean up the document by {self.action_verb} the following:
            <document>{context["document"]}</document>
            <things_to_{self.feedback_type}>{context[f"things_to_{self.feedback_type}"]}</things_to_{self.feedback_type}>
            <style>{writing_style}</style>
        """
        messages = [{"role": "user", "content": prompt}]
        return call_llm_thinking(messages)

    def post(self, shared, prep_res, exec_res):
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n {self.node_name} Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print(f"\n {self.node_name} Skipped - Nothing to {self.feedback_type}")
        
        # Clear the feedback list after processing
        shared["feedback"][f"things_to_{self.feedback_type}"] = []
        return None


class ThingsToRemoveNode(FeedbackNode):
    def __init__(self):
        super().__init__("remove", "removing")

class ThingsToAddNode(FeedbackNode):
    def __init__(self):
        super().__init__("add", "adding")

class ThingsToChangeNode(FeedbackNode):
    def __init__(self):
        super().__init__("change", "changing")

class GroupEvaluatorNode(Node):
    def prep(self, shared):
        print("\n Group Evaluator Node")
        if shared["context"] == "":
            return None

        return {
            "context": shared["context"], 
            "document": shared["document"]
        }

    def exec(self, context):
        if context is None:
            return None
        
        # Call LLM with the entire conversation history
        writing_style = "Write the documents adhering to the writing style of Elements of Style."
        prompt = f"""
            Create or update the document based on the following context and document:
            <context>{context["context"]}</context>
            <document>{context["document"]}</document>
            <style>{writing_style}</style>
        """
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        return response

    def post(self, shared, prep_res, exec_res):
        # count the number of words in exec_res
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n Group Evaluator Node Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print("\n Group Evaluator Node Skipped - No context provided")
        return 'ready_for_committee'

# Create nodes
group_lead_node = GroupLeadNode()
document_drafting_node = DocumentDraftingNode()
things_to_remove_node = ThingsToRemoveNode()
things_to_add_node = ThingsToAddNode()
things_to_change_node = ThingsToChangeNode()
group_evaluator_node = GroupEvaluatorNode()

# Connect nodes
group_lead_node >> things_to_remove_node
group_lead_node - "abandon" >> None
things_to_remove_node >> things_to_add_node
things_to_add_node >> things_to_change_node
things_to_change_node >> document_drafting_node
document_drafting_node >> group_evaluator_node
group_evaluator_node - "rejected" >> group_lead_node

# Create flow
working_group_flow = Flow(start=group_lead_node)
