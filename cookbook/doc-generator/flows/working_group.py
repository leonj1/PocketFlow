from pocketflow import Node, Flow
import sys
sys.path.append('/app/cookbook/doc-generator')
from utils import call_llm, call_llm_thinking

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
        
        # Call LLM with the entire conversation history
        writing_style = "Write the documents adhering to the writing style of Elements of Style."
        prompt = f"""
            Draft a document based on the following context:
            <context>{context}</context>
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

class ThingsToRemoveNode(Node):
    def prep(self, shared):
        print("\n Things To Remove Node")
        # If there are things to remove from the shared variable, add it to a variable. 
        if shared["feedback"]["things_to_remove"] == "":
            return None

        return {
            "document": shared["document"], 
            "things_to_remove": shared["feedback"]["things_to_remove"]
        }

    def exec(self, context):
        if context is None:
            return None
        
        # Call LLM with the entire conversation history
        prompt = f"""
            Clean up the document by removing the following:
            <document>{context["document"]}</document>
            <things_to_remove>{context["things_to_remove"]}</things_to_remove>
        """
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        return response

    def post(self, shared, prep_res, exec_res):
        # count the number of words in exec_res
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n Things to Remove Node Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print("\n Things to Remove Node Skipped - Nothing to remove")
        return None

class ThingsToAddNode(Node):
    def prep(self, shared):
        print("\n Things To Add Node")
        # If there are things to remove from the shared variable, add it to a variable. 
        if shared["feedback"]["things_to_add"] == "":
            return None

        return {
            "document": shared["document"], 
            "things_to_add": shared["feedback"]["things_to_add"]
        }

    def exec(self, context):
        if context is None:
            return None
        
        # Call LLM with the entire conversation history
        prompt = f"""
            Clean up the document by adding the following:
            <document>{context["document"]}</document>
            <things_to_add>{context["things_to_add"]}</things_to_add>
        """
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        return response

    def post(self, shared, prep_res, exec_res):
        # count the number of words in exec_res
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n Things to Add Node Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print("\n Things to Add Node Skipped - Nothing to add")
        # clear things to add
        shared["feedback"]["things_to_add"] = ""
        return None

class ThingsToChangeNode(Node):
    def prep(self, shared):
        print("\n Things To Change Node")
        # If there are things to change from the shared variable, add it to a variable. 
        if shared["feedback"]["things_to_change"] == "":
            return None

        return {
            "document": shared["document"], 
            "things_to_change": shared["feedback"]["things_to_change"]
        }

    def exec(self, context):
        if context is None:
            return None
        
        # Call LLM with the entire conversation history
        prompt = f"""
            Clean up the document by changing the following:
            <document>{context["document"]}</document>
            <things_to_change>{context["things_to_change"]}</things_to_change>
        """
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        return response

    def post(self, shared, prep_res, exec_res):
        # count the number of words in exec_res
        if exec_res is not None:
            word_count = len(exec_res.split())
            print(f"\n Things to Change Node Completed. Word Count: {word_count}")
            shared["document"] = exec_res
        else:
            print("\n Things to Change Node Skipped - Nothing to change")
        # clear things to change
        shared["feedback"]["things_to_change"] = ""
        return None

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
