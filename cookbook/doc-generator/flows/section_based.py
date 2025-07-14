from pocketflow import Node, Flow, AsyncNode, AsyncFlow
import asyncio
import sys
sys.path.append('/app/cookbook/doc-generator')
from utils import call_llm, call_llm_thinking
import yaml
import json

class SectionData:
    """Data structure to hold section-specific information"""
    def __init__(self, section_config):
        self.name = section_config["name"]
        self.max_pages = section_config.get("max_pages", 3)
        self.audience_focus = section_config.get("audience_focus", ["All"])
        self.content = ""
        self.status = "pending"  # pending, in_progress, completed, needs_revision
        self.dependencies = []  # List of other section names this depends on
        self.feedback = {
            "things_to_remove": [],
            "things_to_add": [],
            "things_to_change": []
        }
        self.word_count = 0
        self.version = 0

class SectionCoordinatorNode(Node):
    """Manages section dependencies and prevents duplication across sections"""
    
    def prep(self, shared):
        print("\n Section Coordinator Node")
        
        # Initialize section data if not present
        if "sections" not in shared:
            sections_config = shared["context"]["deliverables"][0]["sections"]
            shared["sections"] = {}
            for section_config in sections_config:
                section_name = section_config["name"]
                shared["sections"][section_name] = SectionData(section_config).__dict__
        
        # Find sections ready to be drafted (no pending dependencies)
        ready_sections = []
        for section_name, section_data in shared["sections"].items():
            if section_data["status"] == "pending":
                # Check if all dependencies are completed
                deps_ready = all(
                    shared["sections"].get(dep, {}).get("status") == "completed" 
                    for dep in section_data.get("dependencies", [])
                )
                if deps_ready:
                    ready_sections.append(section_name)
        
        if not ready_sections:
            return None
            
        return {
            "ready_sections": ready_sections,
            "all_sections": list(shared["sections"].keys()),
            "completed_sections": {
                name: {"summary": data.get("content", "")[:200] + "...", 
                       "key_points": data.get("key_points", [])}
                for name, data in shared["sections"].items() 
                if data["status"] == "completed"
            }
        }
    
    def post(self, shared, prep_res, exec_res):
        if prep_res:
            # Mark ready sections as available for processing
            shared["sections_to_process"] = prep_res["ready_sections"]
            print(f"Sections ready for processing: {prep_res['ready_sections']}")
        return None

class SectionDraftingNode(AsyncNode):
    """Drafts individual sections with awareness of other sections"""
    
    async def prep_async(self, shared):
        print("\n Section Drafting Node")
        
        if "sections_to_process" not in shared or not shared["sections_to_process"]:
            return None
            
        # Get next section to process
        section_name = shared["sections_to_process"][0]
        section_data = shared["sections"][section_name]
        
        # Mark as in_progress
        section_data["status"] = "in_progress"
        
        # Gather context about other sections
        other_sections_info = {}
        for name, data in shared["sections"].items():
            if name != section_name:
                other_sections_info[name] = {
                    "status": data["status"],
                    "summary": data.get("content", "")[:200] + "..." if data.get("content") else "Not yet drafted",
                    "key_points": data.get("key_points", [])
                }
        
        return {
            "section_name": section_name,
            "section_config": section_data,
            "context": shared["context"],
            "other_sections": other_sections_info,
            "completed_sections": {
                name: data["content"] 
                for name, data in shared["sections"].items() 
                if data["status"] == "completed"
            }
        }
    
    async def exec_async(self, prep_data):
        if not prep_data:
            return None
            
        section_name = prep_data["section_name"]
        section_config = prep_data["section_config"]
        context = prep_data["context"]
        
        # Build section-specific prompt
        writing_style = "Write the documents adhering to the writing style of Elements of Style."
        
        # Check if this is a revision (has feedback)
        is_revision = section_config.get("version", 0) > 0
        has_feedback = any(
            section_config.get("feedback", {}).get(key, []) 
            for key in ["things_to_remove", "things_to_add", "things_to_change"]
        )
        
        # Build revision context if applicable
        revision_context = ""
        if is_revision and has_feedback:
            revision_context = f"""
        <revision_context>
        This is a REVISION of a previously drafted section. The previous version has been reviewed and requires the following changes:
        
        Previous Content:
        {section_config.get("content", "No previous content available")}
        
        Required Changes:
        """
            feedback = section_config.get("feedback", {})
            
            if feedback.get("things_to_remove"):
                revision_context += f"\n        Things to Remove:\n"
                for item in feedback["things_to_remove"]:
                    if item:  # Skip empty items
                        revision_context += f"        - {item}\n"
            
            if feedback.get("things_to_add"):
                revision_context += f"\n        Things to Add:\n"
                for item in feedback["things_to_add"]:
                    if item:  # Skip empty items
                        revision_context += f"        - {item}\n"
            
            if feedback.get("things_to_change"):
                revision_context += f"\n        Things to Change:\n"
                for item in feedback["things_to_change"]:
                    if item:  # Skip empty items
                        revision_context += f"        - {item}\n"
            
            revision_context += """
        
        IMPORTANT: You must address ALL the feedback points above while maintaining the section's core purpose and audience focus.
        </revision_context>
        """
        
        # Adjust the main instruction based on whether this is a revision
        main_instruction = "Revise" if is_revision and has_feedback else "Draft"
        
        prompt = f"""
        You are {main_instruction.lower()}ing the "{section_name}" section of a technical document.
        
        <document_context>
        Topic: {context["topic"]}
        Purpose: {context["purpose"]}
        Document Type: {context["document_type"]}
        </document_context>
        
        <section_requirements>
        Section Name: {section_name}
        Target Audience: {', '.join(section_config["audience_focus"])}
        Maximum Pages: {section_config["max_pages"]}
        </section_requirements>
        {revision_context}
        <other_sections>
        These are the other sections in the document to ensure no duplication:
        {json.dumps(prep_data["other_sections"], indent=2)}
        </other_sections>
        
        <completed_sections>
        These sections have already been written:
        {json.dumps(list(prep_data["completed_sections"].keys()))}
        </completed_sections>
        
        <terminology>
        Key terms to use consistently:
        {json.dumps({term["term"]: term["definition"] for term in context.get("terminology", [])})}
        </terminology>
        
        <writing_style>{writing_style}</writing_style>
        
        {main_instruction} the "{section_name}" section now. Focus on:
        1. Content specific to this section only
        2. Avoid duplicating content from other sections
        3. Reference other sections when appropriate
        4. Maintain consistency with document terminology
        5. Target the specified audience
        {"6. Address ALL feedback points from the revision context" if is_revision and has_feedback else ""}
        
        At the end, provide a JSON block with key points covered in this section:
        ```json
        {{
            "key_points": ["point1", "point2", "point3"]
        }}
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = call_llm_thinking(messages)
        
        # Extract key points if present
        key_points = []
        if "```json" in response:
            try:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_data = json.loads(response[json_start:json_end])
                key_points = json_data.get("key_points", [])
                # Remove JSON block from content
                response = response[:response.find("```json")].strip()
            except:
                pass
        
        return {
            "section_name": section_name,
            "content": response,
            "key_points": key_points,
            "word_count": len(response.split())
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        if exec_res:
            section_name = exec_res["section_name"]
            section_data = shared["sections"][section_name]
            
            # Update section data
            section_data["content"] = exec_res["content"]
            section_data["key_points"] = exec_res["key_points"]
            section_data["word_count"] = exec_res["word_count"]
            section_data["status"] = "completed"
            section_data["version"] += 1
            
            # Clear feedback after successful revision
            if section_data["version"] > 1:  # This was a revision
                section_data["feedback"] = {
                    "things_to_remove": [],
                    "things_to_add": [],
                    "things_to_change": []
                }
                print(f"Section '{section_name}' revised (v{section_data['version']}). Word count: {exec_res['word_count']}")
            else:
                print(f"Section '{section_name}' completed. Word count: {exec_res['word_count']}")
            
            # Remove from processing queue
            shared["sections_to_process"].remove(section_name)
        
        return None

class SectionReviewNode(AsyncNode):
    """Reviews individual sections for quality and consistency"""
    
    async def prep_async(self, shared):
        print("\n Section Review Node")
        
        # Find completed sections that haven't been reviewed
        sections_to_review = [
            name for name, data in shared["sections"].items()
            if data["status"] == "completed" and data.get("review_status") != "reviewed"
        ]
        
        if not sections_to_review:
            return None
            
        section_name = sections_to_review[0]
        section_data = shared["sections"][section_name]
        
        return {
            "section_name": section_name,
            "section_content": section_data["content"],
            "section_config": section_data,
            "context": shared["context"],
            "other_sections": {
                name: data.get("key_points", [])
                for name, data in shared["sections"].items()
                if name != section_name
            }
        }
    
    async def exec_async(self, prep_data):
        if not prep_data:
            return None
            
        prompt = f"""
        Review the following section for quality and consistency:
        
        Section: {prep_data["section_name"]}
        
        <section_content>
        {prep_data["section_content"]}
        </section_content>
        
        <requirements>
        - Target audience: {', '.join(prep_data["section_config"]["audience_focus"])}
        - Maximum pages: {prep_data["section_config"]["max_pages"]}
        - Current word count: {prep_data["section_config"]["word_count"]}
        </requirements>
        
        <other_sections_key_points>
        {json.dumps(prep_data["other_sections"], indent=2)}
        </other_sections_key_points>
        
        Review for:
        1. Completeness for the target audience
        2. No duplication with other sections
        3. Appropriate length
        4. Technical accuracy
        5. Clarity and coherence
        
        Provide feedback in YAML format:
        ```yaml
        quality_score: [1-10]
        things_to_remove: "specific content to remove"
        things_to_add: "specific content to add"
        things_to_change: "specific changes needed"
        approval: "approved" or "needs_revision"
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = call_llm(messages)
        
        # Parse YAML response
        try:
            yaml_start = response.find("```yaml") + 7
            yaml_end = response.find("```", yaml_start)
            yaml_data = yaml.safe_load(response[yaml_start:yaml_end])
            return {
                "section_name": prep_data["section_name"],
                "review": yaml_data
            }
        except:
            return {
                "section_name": prep_data["section_name"],
                "review": {
                    "quality_score": 7,
                    "approval": "approved"
                }
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        if exec_res:
            section_name = exec_res["section_name"]
            section_data = shared["sections"][section_name]
            review = exec_res["review"]
            
            section_data["review_status"] = "reviewed"
            section_data["quality_score"] = review.get("quality_score", 7)
            
            if review.get("approval") == "needs_revision":
                section_data["status"] = "needs_revision"
                section_data["feedback"]["things_to_remove"].append(review.get("things_to_remove", ""))
                section_data["feedback"]["things_to_add"].append(review.get("things_to_add", ""))
                section_data["feedback"]["things_to_change"].append(review.get("things_to_change", ""))
                print(f"Section '{section_name}' needs revision. Quality score: {review.get('quality_score')}/10")
            else:
                print(f"Section '{section_name}' approved. Quality score: {review.get('quality_score')}/10")
        
        return None

class DocumentAssemblerNode(Node):
    """Combines all sections into a coherent final document"""
    
    def prep(self, shared):
        print("\n Document Assembler Node")
        
        # Check if all sections are completed and reviewed
        all_sections = shared["sections"]
        incomplete_sections = [
            name for name, data in all_sections.items()
            if data["status"] != "completed" or data.get("review_status") != "reviewed"
        ]
        
        if incomplete_sections:
            print(f"Cannot assemble document. Incomplete sections: {incomplete_sections}")
            return None
            
        return {
            "sections": all_sections,
            "context": shared["context"]
        }
    
    def exec(self, prep_data):
        if not prep_data:
            return None
            
        sections = prep_data["sections"]
        context = prep_data["context"]
        
        # Assemble document in order
        document_parts = []
        
        # Add title
        document_parts.append(f"# {context['topic']}\n")
        document_parts.append(f"**Document Type:** {context['document_type']}")
        document_parts.append(f"**Version:** {context['version']}\n")
        
        # Add sections in order
        section_order = [s["name"] for s in context["deliverables"][0]["sections"]]
        
        for section_name in section_order:
            if section_name in sections:
                section_data = sections[section_name]
                document_parts.append(f"\n## {section_name}\n")
                document_parts.append(section_data["content"])
        
        # Add metadata
        document_parts.append("\n---\n")
        document_parts.append("### Document Metadata\n")
        
        total_words = sum(s["word_count"] for s in sections.values())
        avg_quality = sum(s.get("quality_score", 7) for s in sections.values()) / len(sections)
        
        document_parts.append(f"- Total Word Count: {total_words}")
        document_parts.append(f"- Average Section Quality: {avg_quality:.1f}/10")
        document_parts.append(f"- Sections: {len(sections)}")
        
        return "\n".join(document_parts)
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared["document"] = exec_res
            word_count = len(exec_res.split())
            print(f"Document assembled successfully. Total word count: {word_count}")
        return None

# Create parallel section processing flow
class ParallelSectionFlow(AsyncFlow):
    """Manages parallel processing of multiple sections"""
    
    async def run_async(self, shared):
        print("\n Starting Parallel Section Processing")
        
        # Get sections to process
        sections_to_process = shared.get("sections_to_process", [])
        
        if not sections_to_process:
            print("No sections to process")
            return None
        
        print(f"Sections in queue: {len(sections_to_process)} - {sections_to_process[:5]}...")  # Show first 5
            
        # Create drafting tasks for each section
        drafting_tasks = []
        for section_name in sections_to_process[:3]:  # Process up to 3 sections in parallel
            node = SectionDraftingNode()
            task = asyncio.create_task(self._process_section(node, shared, section_name))
            drafting_tasks.append(task)
        
        # Wait for all sections to complete
        results = await asyncio.gather(*drafting_tasks)
        
        print(f"Completed {len(results)} sections in parallel")
        return None  # Continue to next node in workflow
    
    async def _process_section(self, node, shared, section_name):
        """Process a single section"""
        # Create a copy of shared for this specific section
        section_shared = shared.copy()
        section_shared["sections_to_process"] = [section_name]
        
        prep_res = await node.prep_async(section_shared)
        if prep_res:
            exec_res = await node.exec_async(prep_res)
            await node.post_async(shared, prep_res, exec_res)  # Update main shared
            return exec_res
        return None

# Create flow nodes
section_coordinator = SectionCoordinatorNode()
section_drafting = SectionDraftingNode()
section_review = SectionReviewNode()
document_assembler = DocumentAssemblerNode()

# Create flows
section_based_flow = Flow(start=section_coordinator)
section_coordinator >> section_drafting
section_drafting >> section_review
section_review >> document_assembler

# Parallel processing wrapper
class ParallelSectionNode(Node):
    def __init__(self):
        super().__init__()
        self.async_flow = ParallelSectionFlow(start=section_drafting)
    
    def post(self, shared, prep_res, exec_res):
        result = asyncio.run(self.async_flow.run_async(shared))
        return result

parallel_section_node = ParallelSectionNode()