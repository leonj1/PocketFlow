"""
Web Search Service for PocketFlow Document Workflow.

This module provides web search capabilities using SerpAPI (Google Search)
for all document workflow nodes.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Import SerpAPI client
try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None
    print("Warning: serpapi package not installed. Web search will be disabled.")

# Set up logging
logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, title: str, snippet: str, url: str, position: int = 0):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.position = position
        self.relevance_score = 1.0 / (position + 1)  # Simple relevance based on position
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "position": self.position,
            "relevance_score": self.relevance_score
        }
    
    def __repr__(self) -> str:
        return f"SearchResult(title='{self.title[:30]}...', url='{self.url}')"


class WebSearchService:
    """Service class for web search functionality using SerpAPI."""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 max_results: Optional[int] = None,
                 enabled: Optional[bool] = None):
        """
        Initialize the Web Search Service.
        
        Args:
            api_key: SerpAPI key (falls back to SERPAPI_API_KEY env var)
            max_results: Maximum number of results to return (falls back to WEB_SEARCH_MAX_RESULTS env var)
            enabled: Whether search is enabled (falls back to WEB_SEARCH_ENABLED env var)
        """
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        self.max_results = max_results or int(os.getenv('WEB_SEARCH_MAX_RESULTS', '5'))
        self.enabled = enabled if enabled is not None else os.getenv('WEB_SEARCH_ENABLED', 'true').lower() == 'true'
        
        # Check if search can be enabled
        if self.enabled:
            if not self.api_key:
                logger.warning("Web search disabled: SERPAPI_API_KEY not found")
                self.enabled = False
            elif GoogleSearch is None:
                logger.warning("Web search disabled: serpapi package not installed")
                self.enabled = False
            else:
                logger.info(f"Web search service initialized (max_results: {self.max_results})")
                print(f"🔍 Web Search Service initialized (enabled: {self.enabled}, max_results: {self.max_results})")
        else:
            logger.info("Web search service disabled by configuration")
            print("🔍 Web Search Service disabled by configuration")
    
    def is_enabled(self) -> bool:
        """Check if web search is enabled."""
        return self.enabled
    
    def search(self, 
               query: str, 
               search_type: str = "general",
               num_results: Optional[int] = None,
               **kwargs) -> List[SearchResult]:
        """
        Perform a web search.
        
        Args:
            query: Search query string
            search_type: Type of search (general, academic, standards, technical)
            num_results: Number of results to return (overrides max_results)
            **kwargs: Additional parameters for SerpAPI
            
        Returns:
            List of SearchResult objects
        """
        if not self.enabled:
            logger.debug(f"Search skipped (disabled): {query}")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []
        
        # Determine number of results
        num_results = num_results or self.max_results
        
        # Enhance query based on search type
        enhanced_query = self._enhance_query(query, search_type)
        
        # Set up search parameters
        params = {
            "engine": "google",
            "q": enhanced_query,
            "api_key": self.api_key,
            "num": num_results,
            **kwargs  # Allow additional parameters
        }
        
        # Add specific parameters based on search type
        if search_type == "academic":
            params["tbm"] = "scholar"  # Google Scholar search
        elif search_type == "standards":
            params["q"] += " site:iso.org OR site:ietf.org OR site:w3.org"
        
        try:
            logger.info(f"Searching for: {enhanced_query} (type: {search_type})")
            
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Process results
            search_results = self._process_results(results, search_type)
            
            logger.info(f"Found {len(search_results)} results for: {query}")
            return search_results[:num_results]
            
        except Exception as e:
            logger.error(f"Search error for '{query}': {str(e)}")
            print(f"  ✗ Web search failed: {str(e)}")
            return []
    
    def search_similar_standards(self, topic: str, scope: List[str]) -> List[SearchResult]:
        """
        Search for similar standards and best practices.
        
        Args:
            topic: The main topic of the document
            scope: List of scope items to include
            
        Returns:
            List of relevant standards and guidelines
        """
        # Build query from topic and scope
        query_parts = [topic, "standards", "best practices", "guidelines"]
        if scope:
            query_parts.extend(scope[:2])  # Add first two scope items
        
        query = " ".join(query_parts)
        return self.search(query, search_type="standards", num_results=10)
    
    def search_references(self, section_name: str, context: str) -> List[SearchResult]:
        """
        Search for references and examples for a document section.
        
        Args:
            section_name: Name of the section being drafted
            context: Context about what the section should contain
            
        Returns:
            List of relevant references and examples
        """
        query = f"{section_name} {context} examples implementation guide"
        return self.search(query, search_type="technical", num_results=5)
    
    def search_document_templates(self, document_type: str, industry: Optional[str] = None) -> List[SearchResult]:
        """
        Search for document structure templates.
        
        Args:
            document_type: Type of document (e.g., "Technical Standard", "ADR")
            industry: Industry or domain context
            
        Returns:
            List of relevant document templates and structures
        """
        query_parts = [document_type, "template", "structure", "outline"]
        if industry:
            query_parts.append(industry)
        
        query = " ".join(query_parts)
        return self.search(query, search_type="general", num_results=5)
    
    def verify_references(self, references: List[str]) -> Dict[str, bool]:
        """
        Verify that external references exist and are accessible.
        
        Args:
            references: List of reference URLs or standard names
            
        Returns:
            Dictionary mapping references to verification status
        """
        if not self.enabled:
            return {ref: False for ref in references}
        
        verification_results = {}
        
        for reference in references:
            # Search for the exact reference
            results = self.search(f'"{reference}"', search_type="general", num_results=1)
            
            # Check if we found a match
            if results:
                # Simple verification: check if the reference appears in the results
                found = any(reference.lower() in result.title.lower() or 
                          reference.lower() in result.snippet.lower() 
                          for result in results)
                verification_results[reference] = found
            else:
                verification_results[reference] = False
        
        return verification_results
    
    def _enhance_query(self, query: str, search_type: str) -> str:
        """
        Enhance the search query based on search type.
        
        Args:
            query: Original search query
            search_type: Type of search
            
        Returns:
            Enhanced query string
        """
        enhancements = {
            "technical": "technical documentation implementation",
            "standards": "standard specification RFC",
            "academic": "research paper study",
            "general": ""
        }
        
        enhancement = enhancements.get(search_type, "")
        if enhancement:
            return f"{query} {enhancement}"
        return query
    
    def _process_results(self, raw_results: Dict, search_type: str) -> List[SearchResult]:
        """
        Process raw SerpAPI results into SearchResult objects.
        
        Args:
            raw_results: Raw results from SerpAPI
            search_type: Type of search performed
            
        Returns:
            List of SearchResult objects
        """
        processed_results = []
        
        # Determine which results key to use based on search type
        if search_type == "academic" and "organic_results" in raw_results:
            results_key = "organic_results"
        else:
            results_key = "organic_results"
        
        if results_key not in raw_results:
            logger.warning(f"No {results_key} found in search results")
            return []
        
        # Process each result
        for i, result in enumerate(raw_results[results_key]):
            try:
                # Extract common fields
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                url = result.get("link", "")
                
                # Skip if essential fields are missing
                if not title or not url:
                    continue
                
                # Create SearchResult object
                search_result = SearchResult(
                    title=title,
                    snippet=snippet,
                    url=url,
                    position=i
                )
                
                processed_results.append(search_result)
                
            except Exception as e:
                logger.error(f"Error processing result {i}: {str(e)}")
                continue
        
        return processed_results
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return {
            "enabled": self.enabled,
            "max_results": self.max_results,
            "api_key_present": bool(self.api_key)
        }


# Singleton instance for easy access
_default_search_service: Optional[WebSearchService] = None


def get_search_service() -> WebSearchService:
    """Get or create the default search service instance."""
    global _default_search_service
    if _default_search_service is None:
        _default_search_service = WebSearchService()
    return _default_search_service


def reset_search_service():
    """Reset the default search service (useful for testing)."""
    global _default_search_service
    _default_search_service = None