"""
Specialized AI agents for document workflow operations.
"""

import asyncio
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from ai_agent import AiAgent
from web_search_service import WebSearchService, SearchResult, get_search_service
import logging
import json

logger = logging.getLogger(__name__)


class DocumentSection(BaseModel):
    """Schema for document sections."""
    title: str = Field(description="Section title")
    content: str = Field(description="Full content of the section")
    audience_focus: List[str] = Field(description="Target audience for this section")
    key_points: List[str] = Field(description="Key points covered in the section")
    estimated_pages: float = Field(description="Estimated page count")


class ReviewFeedback(BaseModel):
    """Schema for review feedback."""
    overall_assessment: str = Field(description="Overall assessment: Excellent, Good, Needs Improvement, Poor")
    strengths: List[str] = Field(description="Document strengths")
    issues: List[str] = Field(description="Issues found")
    suggestions: List[str] = Field(description="Improvement suggestions")
    approval_recommendation: bool = Field(description="Whether to approve the document")
    confidence_score: float = Field(description="Confidence in the review (0-1)")


class NeedsAssessment(BaseModel):
    """Schema for needs assessment output."""
    identified_needs: List[str] = Field(description="List of identified needs")
    priority_areas: List[str] = Field(description="High priority areas to focus on")
    potential_challenges: List[str] = Field(description="Potential challenges to address")
    recommended_approach: str = Field(description="Recommended approach for the document")


class DocumentOutline(BaseModel):
    """Schema for document outline."""
    sections: List[Dict[str, Any]] = Field(description="List of document sections")
    total_pages: int = Field(description="Estimated total pages")
    structure_notes: str = Field(description="Notes about the document structure")


class DocumentAiAgent(AiAgent):
    """Specialized AI agent for document operations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the document AI agent with optional search service."""
        super().__init__(*args, **kwargs)
        self.search_service = None
        self._init_search_service()
    
    def _init_search_service(self):
        """Initialize the web search service if enabled."""
        try:
            self.search_service = get_search_service()
            if self.search_service.is_enabled():
                logger.info("Web search service enabled for DocumentAiAgent")
            else:
                logger.info("Web search service disabled")
        except Exception as e:
            logger.error(f"Failed to initialize search service: {e}")
            self.search_service = None
    
    def search_similar_standards(self, context: Dict) -> List[SearchResult]:
        """
        Search for similar standards and best practices related to the document topic.
        
        Args:
            context: Document context from YAML
            
        Returns:
            List of relevant search results
        """
        if not self.search_service or not self.search_service.is_enabled():
            logger.debug("Search service not available for similar standards search")
            return []
        
        try:
            topic = context.get('topic', '')
            scope_includes = context.get('scope', {}).get('includes', [])
            
            results = self.search_service.search_similar_standards(topic, scope_includes)
            logger.info(f"Found {len(results)} similar standards for topic: {topic}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for similar standards: {e}")
            return []
    
    def search_references(self, section_name: str, context: Dict) -> List[SearchResult]:
        """
        Search for references and examples for a specific document section.
        
        Args:
            section_name: Name of the section being drafted
            context: Document context from YAML
            
        Returns:
            List of relevant references
        """
        if not self.search_service or not self.search_service.is_enabled():
            logger.debug("Search service not available for references search")
            return []
        
        try:
            # Build context string from document context
            context_parts = [
                context.get('topic', ''),
                context.get('document_type', ''),
                ' '.join(context.get('scope', {}).get('includes', [])[:3])
            ]
            context_str = ' '.join(filter(None, context_parts))
            
            results = self.search_service.search_references(section_name, context_str)
            logger.info(f"Found {len(results)} references for section: {section_name}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for references: {e}")
            return []
    
    def search_document_templates(self, context: Dict) -> List[SearchResult]:
        """
        Search for document structure templates based on document type.
        
        Args:
            context: Document context from YAML
            
        Returns:
            List of relevant document templates
        """
        if not self.search_service or not self.search_service.is_enabled():
            logger.debug("Search service not available for template search")
            return []
        
        try:
            document_type = context.get('document_type', 'Technical Standard')
            # Extract industry/domain from audience or scope
            audience = context.get('audience', {})
            industry = None
            
            # Try to infer industry from audience roles
            if 'primary' in audience:
                for member in audience['primary']:
                    if isinstance(member, dict) and 'role' in member:
                        if 'Security' in member['role']:
                            industry = 'security'
                            break
                        elif 'Developer' in member['role']:
                            industry = 'software engineering'
                            break
            
            results = self.search_service.search_document_templates(document_type, industry)
            logger.info(f"Found {len(results)} document templates for type: {document_type}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for document templates: {e}")
            return []
    
    def verify_references(self, references: List[str]) -> Dict[str, bool]:
        """
        Verify that external references exist and are accessible.
        
        Args:
            references: List of reference URLs or standard names
            
        Returns:
            Dictionary mapping references to verification status
        """
        if not self.search_service or not self.search_service.is_enabled():
            logger.debug("Search service not available for reference verification")
            return {ref: False for ref in references}
        
        try:
            results = self.search_service.verify_references(references)
            verified_count = sum(1 for v in results.values() if v)
            logger.info(f"Verified {verified_count}/{len(references)} references")
            return results
            
        except Exception as e:
            logger.error(f"Error verifying references: {e}")
            return {ref: False for ref in references}
    
    def format_search_results_for_prompt(self, results: List[SearchResult], max_results: int = 3) -> str:
        """
        Format search results for inclusion in AI prompts.
        
        Args:
            results: List of search results
            max_results: Maximum number of results to include
            
        Returns:
            Formatted string for prompt inclusion
        """
        if not results:
            return "No relevant search results found."
        
        formatted_parts = ["Relevant search results:"]
        for i, result in enumerate(results[:max_results]):
            formatted_parts.append(f"\n{i+1}. {result.title}")
            formatted_parts.append(f"   {result.snippet}")
            formatted_parts.append(f"   URL: {result.url}")
        
        return "\n".join(formatted_parts)
    
    def generate_section(self, 
                        section_name: str, 
                        context: Dict,
                        max_pages: int,
                        previous_sections: Optional[List[str]] = None) -> DocumentSection:
        """
        Generate a document section based on context.
        
        Args:
            section_name: Name of the section to generate
            context: Document context from YAML
            max_pages: Maximum pages for this section
            previous_sections: List of previously generated section summaries
            
        Returns:
            DocumentSection with generated content
        """
        if not self.is_enabled():
            # Return placeholder if AI is disabled
            return DocumentSection(
                title=section_name,
                content=f"[Placeholder content for {section_name}]",
                audience_focus=["All"],
                key_points=["Manual content required"],
                estimated_pages=1.0
            )
        
        try:
            # Build the prompt
            prompt = f"""Generate content for the '{section_name}' section of a technical document.

Document Context:
- Topic: {context.get('topic', 'Not specified')}
- Purpose: {context.get('purpose', 'Not specified')}
- Document Type: {context.get('document_type', 'Technical Standard')}

Target Audience:
{self._format_audience(context.get('audience', {}))}

Scope Includes:
{json.dumps(context.get('scope', {}).get('includes', []), indent=2)}

Constraints:
- Maximum {max_pages} pages for this section
- Must align with: {', '.join(context.get('constraints', {}).get('technical', []))}

"""
            if previous_sections:
                prompt += f"\nPrevious sections covered:\n{chr(10).join(previous_sections)}\n"
            
            prompt += f"""
Please generate:
1. Comprehensive content for the '{section_name}' section
2. Key points that must be covered
3. Appropriate depth for the target audience
4. Professional, clear language

Format the response as a DocumentSection with title, content, audience_focus, key_points, and estimated_pages."""

            # Create specialized agent for structured output
            section_agent = Agent(
                model=self.agent.model if self.agent else None,
                result_type=DocumentSection,
                system_prompt="You are a technical documentation expert creating professional documents."
            )
            
            # Generate the section
            result = asyncio.run(section_agent.run(prompt))
            return result.data
            
        except Exception as e:
            logger.error(f"Error generating section: {e}")
            # Return fallback
            return DocumentSection(
                title=section_name,
                content=f"Error generating content: {str(e)}",
                audience_focus=["All"],
                key_points=["AI generation failed"],
                estimated_pages=1.0
            )
    
    def review_document(self, 
                       document_content: str,
                       context: Dict,
                       review_type: str = "general") -> ReviewFeedback:
        """
        Review a document and provide structured feedback.
        
        Args:
            document_content: The document content to review
            context: Document context from YAML
            review_type: Type of review (general, technical, compliance)
            
        Returns:
            ReviewFeedback with detailed analysis
        """
        if not self.is_enabled():
            return ReviewFeedback(
                overall_assessment="Manual Review Required",
                strengths=["AI review disabled"],
                issues=["Manual review needed"],
                suggestions=["Enable AI for automated review"],
                approval_recommendation=False,
                confidence_score=0.0
            )
        
        try:
            # Build review prompt based on type
            prompt = f"""Review the following document content as a {review_type} reviewer.

Document Context:
- Topic: {context.get('topic', 'Not specified')}
- Purpose: {context.get('purpose', 'Not specified')}
- Target Audience: {self._format_audience(context.get('audience', {}))}

Success Criteria:
{json.dumps(context.get('success_criteria', {}), indent=2)}

Document Content:
{document_content[:3000]}...  # Truncated for review

Please provide a comprehensive review including:
1. Overall assessment (Excellent, Good, Needs Improvement, Poor)
2. Document strengths
3. Issues or gaps identified
4. Specific improvement suggestions
5. Whether you recommend approval
6. Your confidence score (0-1)

Consider:
- Completeness relative to scope
- Clarity for target audience
- Technical accuracy
- Alignment with purpose and constraints"""

            # Create review agent
            review_agent = Agent(
                model=self.agent.model if self.agent else None,
                result_type=ReviewFeedback,
                system_prompt=f"You are an expert {review_type} document reviewer."
            )
            
            # Get review
            result = asyncio.run(review_agent.run(prompt))
            return result.data
            
        except Exception as e:
            logger.error(f"Error reviewing document: {e}")
            return ReviewFeedback(
                overall_assessment="Review Error",
                strengths=[],
                issues=[f"Review failed: {str(e)}"],
                suggestions=["Manual review required"],
                approval_recommendation=False,
                confidence_score=0.0
            )
    
    def assess_needs(self, context: Dict) -> NeedsAssessment:
        """
        Perform intelligent needs assessment based on context.
        
        Args:
            context: Document context from YAML
            
        Returns:
            NeedsAssessment with identified needs and recommendations
        """
        if not self.is_enabled():
            return NeedsAssessment(
                identified_needs=["Manual needs assessment required"],
                priority_areas=["All areas"],
                potential_challenges=["AI disabled"],
                recommended_approach="Manual process"
            )
        
        try:
            prompt = f"""Perform a needs assessment for creating a document with the following context:

Topic: {context.get('topic')}
Purpose: {context.get('purpose')}
Document Type: {context.get('document_type')}

Audience:
{self._format_audience(context.get('audience', {}))}

Scope:
{json.dumps(context.get('scope', {}), indent=2)}

Constraints:
{json.dumps(context.get('constraints', {}), indent=2)}

Based on this context, identify:
1. Key needs that must be addressed
2. Priority areas to focus on
3. Potential challenges in creating this document
4. Recommended approach for maximum effectiveness"""

            needs_agent = Agent(
                model=self.agent.model if self.agent else None,
                result_type=NeedsAssessment,
                system_prompt="You are a document planning expert."
            )
            
            result = asyncio.run(needs_agent.run(prompt))
            return result.data
            
        except Exception as e:
            logger.error(f"Error in needs assessment: {e}")
            return NeedsAssessment(
                identified_needs=[f"Assessment error: {str(e)}"],
                priority_areas=[],
                potential_challenges=["AI assessment failed"],
                recommended_approach="Manual assessment required"
            )
    
    def generate_outline(self, context: Dict, needs: List[str]) -> DocumentOutline:
        """
        Generate an intelligent document outline.
        
        Args:
            context: Document context from YAML
            needs: Identified needs from assessment
            
        Returns:
            DocumentOutline with structured sections
        """
        if not self.is_enabled():
            # Use deliverables from context as fallback
            deliverables = context.get('deliverables', [])
            sections = []
            
            for deliverable in deliverables:
                if deliverable.get('type') == 'Main Document':
                    sections = deliverable.get('sections', [])
                    break
            
            return DocumentOutline(
                sections=sections,
                total_pages=25,
                structure_notes="Generated from context deliverables"
            )
        
        try:
            prompt = f"""Generate a detailed document outline based on:

Topic: {context.get('topic')}
Purpose: {context.get('purpose')}
Identified Needs: {json.dumps(needs, indent=2)}

Deliverable Requirements:
{json.dumps(context.get('deliverables', []), indent=2)}

Create an outline that:
1. Addresses all identified needs
2. Follows a logical structure
3. Allocates appropriate pages per section
4. Considers the target audience
5. Stays within total page constraints

Return a structured outline with sections, page allocations, and structure notes."""

            outline_agent = Agent(
                model=self.agent.model if self.agent else None,
                result_type=DocumentOutline,
                system_prompt="You are a document structure expert."
            )
            
            result = asyncio.run(outline_agent.run(prompt))
            return result.data
            
        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            # Fallback to context-based outline
            return self.generate_outline(context, needs)
    
    def _format_audience(self, audience: Dict) -> str:
        """Format audience information for prompts."""
        lines = []
        for aud_type, members in audience.items():
            lines.append(f"{aud_type.capitalize()}:")
            for member in members:
                if isinstance(member, dict):
                    role = member.get('role', 'Unknown')
                    level = member.get('experience_level', 'All')
                    lines.append(f"  - {role} ({level})")
                else:
                    lines.append(f"  - {member}")
        return "\n".join(lines)


# Convenience function
def get_document_ai_agent() -> DocumentAiAgent:
    """Get a document-specific AI agent instance."""
    return DocumentAiAgent()