from pocketflow import Node, Flow, AsyncNode
import sys
sys.path.append('/app/cookbook/doc-generator')
from completeness_utils import (
    ReadabilityAnalyzer, 
    ConceptualGraphBuilder, 
    GoalTracker, 
    ScopeComplianceChecker
)
from utils import call_llm, call_llm_thinking
import json
import yaml

class DocumentCompletenessNode(Node):
    """Analyzes document completeness across multiple dimensions"""
    
    def prep(self, shared):
        print("\n Document Completeness Analysis Node")
        
        # Check if we have content to analyze
        if "sections" not in shared and "document" not in shared:
            return None
        
        # Initialize analyzers
        context = shared["context"]
        terminology = context.get("terminology", [])
        
        return {
            "context": context,
            "sections": shared.get("sections", {}),
            "document": shared.get("document", ""),
            "terminology": terminology,
            "mode": "sections" if "sections" in shared else "document"
        }
    
    def exec(self, prep_data):
        if not prep_data:
            return None
        
        # Initialize analyzers
        readability_analyzer = ReadabilityAnalyzer()
        concept_builder = ConceptualGraphBuilder(prep_data["terminology"])
        goal_tracker = GoalTracker(prep_data["context"])
        scope_checker = ScopeComplianceChecker(prep_data["context"])
        
        results = {
            "readability_issues": [],
            "conceptual_gaps": [],
            "unfulfilled_goals": [],
            "scope_violations": [],
            "overall_completeness": 0,
            "section_analyses": {}
        }
        
        if prep_data["mode"] == "sections":
            # Analyze each section
            for section_name, section_data in prep_data["sections"].items():
                if section_data["status"] != "completed":
                    continue
                
                section_results = self._analyze_section(
                    section_name,
                    section_data,
                    readability_analyzer,
                    concept_builder,
                    goal_tracker,
                    scope_checker
                )
                
                results["section_analyses"][section_name] = section_results
                
                # Aggregate issues
                results["readability_issues"].extend(section_results["readability_issues"])
                results["scope_violations"].extend(section_results["scope_violations"])
            
            # Document-wide analyses
            self._analyze_document_wide(
                prep_data["sections"],
                concept_builder,
                goal_tracker,
                results
            )
        else:
            # Analyze full document
            doc_results = self._analyze_full_document(
                prep_data["document"],
                prep_data["context"],
                readability_analyzer,
                concept_builder,
                goal_tracker,
                scope_checker
            )
            results.update(doc_results)
        
        # Calculate overall completeness score
        results["overall_completeness"] = self._calculate_completeness_score(results)
        
        return results
    
    def _analyze_section(self, section_name, section_data, readability, concepts, goals, scope):
        """Analyze a single section"""
        content = section_data.get("content", "")
        audience = section_data.get("audience_focus", ["All"])
        
        analysis = {
            "section_name": section_name,
            "readability_issues": [],
            "scope_violations": [],
            "concepts_found": set()
        }
        
        # Readability analysis
        for target_audience in audience:
            readability_check = readability.check_audience_match(content, target_audience)
            if not readability_check["match"]:
                analysis["readability_issues"].append({
                    "section": section_name,
                    "audience": target_audience,
                    "issue": readability_check["message"],
                    "suggestion": readability_check.get("suggestion", "")
                })
        
        # Extract concepts for this section
        section_concepts = concepts.extract_concepts(content, section_name)
        analysis["concepts_found"] = section_concepts
        
        # Build concept relationships within section
        concepts.build_relationships(content, section_concepts)
        
        # Check scope compliance
        scope_issues = scope.check_scope_compliance(content, section_name)
        analysis["scope_violations"].extend(scope_issues)
        
        # Goal fulfillment (section-specific)
        goal_check = goals.check_goal_fulfillment(content, section_name)
        analysis["section_goal_fulfillment"] = goal_check["fulfillment_rate"]
        
        return analysis
    
    def _analyze_document_wide(self, sections, concepts, goals, results):
        """Perform document-wide analyses"""
        # Analyze conceptual gaps across all sections
        conceptual_gaps = concepts.analyze_conceptual_gaps()
        results["conceptual_gaps"] = conceptual_gaps
        
        # Check overall goal fulfillment
        all_content = " ".join(
            section["content"] 
            for section in sections.values() 
            if section["status"] == "completed"
        )
        
        goal_results = goals.check_goal_fulfillment(all_content)
        results["unfulfilled_goals"] = [
            {
                "goal": goal["description"],
                "type": goal["type"],
                "suggestion": f"Address '{goal['description']}' in appropriate section"
            }
            for goal in goal_results["unfulfilled"]
        ]
        results["goal_fulfillment_rate"] = goal_results["fulfillment_rate"]
    
    def _analyze_full_document(self, document, context, readability, concepts, goals, scope):
        """Analyze a complete document"""
        results = {
            "readability_issues": [],
            "conceptual_gaps": [],
            "unfulfilled_goals": [],
            "scope_violations": []
        }
        
        # Overall readability
        primary_audience = context.get("audience", {}).get("primary", [{}])[0].get("role", "All")
        readability_check = readability.check_audience_match(document, primary_audience)
        if not readability_check["match"]:
            results["readability_issues"].append({
                "section": "Full Document",
                "issue": readability_check["message"],
                "suggestion": readability_check.get("suggestion", "")
            })
        
        # Extract and analyze concepts
        doc_concepts = concepts.extract_concepts(document)
        concepts.build_relationships(document, doc_concepts)
        results["conceptual_gaps"] = concepts.analyze_conceptual_gaps()
        
        # Goal fulfillment
        goal_results = goals.check_goal_fulfillment(document)
        results["unfulfilled_goals"] = [
            {
                "goal": goal["description"],
                "type": goal["type"]
            }
            for goal in goal_results["unfulfilled"]
        ]
        results["goal_fulfillment_rate"] = goal_results["fulfillment_rate"]
        
        # Scope compliance
        results["scope_violations"] = scope.check_scope_compliance(document)
        
        return results
    
    def _calculate_completeness_score(self, results):
        """Calculate overall completeness score (0-100)"""
        scores = []
        
        # Readability score (no issues = 100)
        readability_score = 100 - (len(results["readability_issues"]) * 10)
        scores.append(max(0, readability_score))
        
        # Conceptual coherence score (no gaps = 100)
        concept_score = 100 - (len(results["conceptual_gaps"]) * 15)
        scores.append(max(0, concept_score))
        
        # Goal fulfillment score
        goal_score = results.get("goal_fulfillment_rate", 0) * 100
        scores.append(goal_score)
        
        # Scope compliance score (no violations = 100)
        scope_score = 100 - (len(results["scope_violations"]) * 20)
        scores.append(max(0, scope_score))
        
        # Calculate weighted average
        weights = [0.2, 0.3, 0.3, 0.2]  # Readability, Concepts, Goals, Scope
        overall = sum(score * weight for score, weight in zip(scores, weights))
        
        return round(overall, 1)
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            print(f"\n Completeness Analysis Complete. Score: {exec_res['overall_completeness']}/100")
            
            # Store results in shared
            shared["completeness_analysis"] = exec_res
            
            # Print summary of issues
            if exec_res["readability_issues"]:
                print(f"  - Readability Issues: {len(exec_res['readability_issues'])}")
            if exec_res["conceptual_gaps"]:
                print(f"  - Conceptual Gaps: {len(exec_res['conceptual_gaps'])}")
            if exec_res["unfulfilled_goals"]:
                print(f"  - Unfulfilled Goals: {len(exec_res['unfulfilled_goals'])}")
            if exec_res["scope_violations"]:
                print(f"  - Scope Violations: {len(exec_res['scope_violations'])}")
            
            # Determine if document meets completeness threshold
            if exec_res["overall_completeness"] < 70:
                return "needs_improvement"
            
        return None


class SectionCompletenessNode(AsyncNode):
    """Lightweight completeness check for individual sections during drafting"""
    
    async def prep_async(self, shared):
        print("\n Section Completeness Check")
        
        # Find recently completed sections that haven't been checked
        if "sections" not in shared:
            return None
        
        sections_to_check = []
        for name, data in shared["sections"].items():
            if (data["status"] == "completed" and 
                not data.get("completeness_checked", False)):
                sections_to_check.append((name, data))
        
        if not sections_to_check:
            return None
        
        return {
            "sections_to_check": sections_to_check,
            "context": shared["context"]
        }
    
    async def exec_async(self, prep_data):
        if not prep_data:
            return None
        
        readability_analyzer = ReadabilityAnalyzer()
        results = []
        
        for section_name, section_data in prep_data["sections_to_check"]:
            content = section_data.get("content", "")
            audience = section_data.get("audience_focus", ["All"])
            
            # Quick readability check
            issues = []
            for target_audience in audience:
                check = readability_analyzer.check_audience_match(content, target_audience)
                if not check["match"]:
                    issues.append(check)
            
            results.append({
                "section": section_name,
                "readability_ok": len(issues) == 0,
                "issues": issues
            })
        
        return results
    
    async def post_async(self, shared, prep_res, exec_res):
        if exec_res:
            for result in exec_res:
                section_name = result["section"]
                shared["sections"][section_name]["completeness_checked"] = True
                
                if not result["readability_ok"]:
                    print(f"  - {section_name}: Readability issues detected")
                    # Add to feedback for revision
                    for issue in result["issues"]:
                        shared["sections"][section_name]["feedback"]["things_to_change"].append(
                            f"[Readability] {issue['message']} {issue.get('suggestion', '')}"
                        )
                    # Mark for revision
                    shared["sections"][section_name]["status"] = "needs_revision"
        
        return None


class CompletenessReportNode(Node):
    """Generates a detailed completeness report"""
    
    def prep(self, shared):
        print("\n Generating Completeness Report")
        
        if "completeness_analysis" not in shared:
            return None
        
        return {
            "analysis": shared["completeness_analysis"],
            "context": shared["context"]
        }
    
    def exec(self, prep_data):
        if not prep_data:
            return None
        
        analysis = prep_data["analysis"]
        context = prep_data["context"]
        
        # Generate detailed report using LLM
        prompt = f"""
        Generate a comprehensive completeness report for a document about: {context['topic']}
        
        Analysis Results:
        - Overall Completeness Score: {analysis['overall_completeness']}/100
        - Readability Issues: {len(analysis['readability_issues'])}
        - Conceptual Gaps: {len(analysis['conceptual_gaps'])}
        - Unfulfilled Goals: {len(analysis['unfulfilled_goals'])}
        - Scope Violations: {len(analysis['scope_violations'])}
        
        Detailed Issues:
        
        Readability Issues:
        {json.dumps(analysis['readability_issues'], indent=2)}
        
        Conceptual Gaps:
        {json.dumps(analysis['conceptual_gaps'], indent=2)}
        
        Unfulfilled Goals:
        {json.dumps(analysis['unfulfilled_goals'], indent=2)}
        
        Scope Violations:
        {json.dumps(analysis['scope_violations'], indent=2)}
        
        Please provide:
        1. Executive summary of completeness status
        2. Critical issues that must be addressed
        3. Recommendations for improvement
        4. Priority order for addressing issues
        """
        
        messages = [{"role": "user", "content": prompt}]
        report = call_llm(messages)
        
        return {
            "report": report,
            "score": analysis["overall_completeness"],
            "critical_issues": self._identify_critical_issues(analysis)
        }
    
    def _identify_critical_issues(self, analysis):
        """Identify the most critical issues to address"""
        critical = []
        
        # Unfulfilled goals are critical
        if analysis["unfulfilled_goals"]:
            critical.append({
                "type": "unfulfilled_goals",
                "count": len(analysis["unfulfilled_goals"]),
                "priority": "high"
            })
        
        # Major readability mismatches are critical
        severe_readability = [
            issue for issue in analysis["readability_issues"]
            if "too complex" in issue.get("issue", "")
        ]
        if severe_readability:
            critical.append({
                "type": "readability_mismatch",
                "count": len(severe_readability),
                "priority": "high"
            })
        
        # Scope violations are critical
        if analysis["scope_violations"]:
            critical.append({
                "type": "scope_violations",
                "count": len(analysis["scope_violations"]),
                "priority": "medium"
            })
        
        return critical
    
    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared["completeness_report"] = exec_res
            print(f"\n Completeness Report Generated")
            print(f"  - Score: {exec_res['score']}/100")
            print(f"  - Critical Issues: {len(exec_res['critical_issues'])}")
            
            # Save report to file
            report_filename = shared["context"]["output_filename"].replace(".md", "_completeness.md")
            with open(report_filename, "w") as f:
                f.write(f"# Document Completeness Report\n\n")
                f.write(f"**Overall Score:** {exec_res['score']}/100\n\n")
                f.write(exec_res["report"])
        
        return None


# Create flow nodes
document_completeness_node = DocumentCompletenessNode()
section_completeness_node = SectionCompletenessNode()
completeness_report_node = CompletenessReportNode()

# Create completeness flow
document_completeness_node >> completeness_report_node
completeness_flow = Flow(start=document_completeness_node)