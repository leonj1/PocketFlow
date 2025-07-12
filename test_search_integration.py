#!/usr/bin/env python3
"""
Integration test for web search capabilities in document workflow.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from web_search_service import WebSearchService, get_search_service
from document_ai_agents import get_document_ai_agent


def test_search_service_standalone():
    """Test the search service independently."""
    print("Testing Web Search Service...")
    print("=" * 60)
    
    # Get search service
    search_service = get_search_service()
    
    # Check configuration
    config = search_service.get_config()
    print(f"Search Service Configuration:")
    print(f"  Enabled: {config['enabled']}")
    print(f"  Max Results: {config['max_results']}")
    print(f"  API Key Present: {config['api_key_present']}")
    
    if not search_service.is_enabled():
        print("\n⚠️  Search service is disabled. Set SERPAPI_API_KEY to enable.")
        return False
    
    # Test general search
    print("\nTesting general search...")
    results = search_service.search("OAuth JWT security best practices", num_results=3)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"  {i+1}. {result.title}")
        print(f"     {result.snippet[:100]}...")
    
    # Test standards search
    print("\nTesting standards search...")
    results = search_service.search_similar_standards(
        "OAuth JWT token reuse prevention",
        ["Authentication", "Authorization", "API Security"]
    )
    print(f"Found {len(results)} standards")
    
    # Test template search
    print("\nTesting template search...")
    results = search_service.search_document_templates("Technical Standard", "security")
    print(f"Found {len(results)} templates")
    
    return True


def test_document_ai_agent_integration():
    """Test the DocumentAiAgent with search integration."""
    print("\nTesting DocumentAiAgent Integration...")
    print("=" * 60)
    
    # Get AI agent
    ai_agent = get_document_ai_agent()
    
    # Test context
    context = {
        "topic": "OAuth JWT token reuse prevention",
        "document_type": "Technical Standard",
        "purpose": "Prevent unauthorized token reuse between services",
        "audience": {
            "primary": [
                {"role": "Security Engineers", "experience_level": "Senior"},
                {"role": "Backend Developers", "experience_level": "Mid to Senior"}
            ]
        },
        "scope": {
            "includes": ["Authentication", "Authorization", "API Security"]
        }
    }
    
    # Test search for similar standards
    print("\nSearching for similar standards via AI agent...")
    results = ai_agent.search_similar_standards(context)
    print(f"Found {len(results)} similar standards")
    
    # Test search for references
    print("\nSearching for references for 'Authentication Guidelines' section...")
    results = ai_agent.search_references("Authentication Guidelines", context)
    print(f"Found {len(results)} references")
    
    # Test search for templates
    print("\nSearching for document templates via AI agent...")
    results = ai_agent.search_document_templates(context)
    print(f"Found {len(results)} templates")
    
    # Test formatting results for prompt
    if results:
        print("\nFormatted results for AI prompt:")
        formatted = ai_agent.format_search_results_for_prompt(results)
        print(formatted)
    
    return True


def test_node_integration():
    """Test a sample node with search capabilities."""
    print("\nTesting Node Integration...")
    print("=" * 60)
    
    # Import nodes
    from document_workflow import NeedsAssessmentNode
    
    # Create a simple shared state
    shared = {
        "context": {
            "topic": "OAuth JWT token reuse prevention",
            "document_type": "Technical Standard",
            "purpose": "Prevent unauthorized token reuse between services",
            "audience": {
                "primary": [
                    {"role": "Security Engineers", "experience_level": "Senior"}
                ]
            },
            "scope": {
                "includes": ["Authentication", "Authorization", "API Security"]
            },
            "constraints": {
                "timeline": "4 weeks"
            }
        },
        "document": {}
    }
    
    # Create and test node
    node = NeedsAssessmentNode()
    
    print("Testing if AI agent has search service...")
    if node.ai_agent and hasattr(node.ai_agent, 'search_service'):
        if node.ai_agent.search_service and node.ai_agent.search_service.is_enabled():
            print("✓ Search service is available in node")
        else:
            print("✗ Search service is disabled in node")
    else:
        print("✗ AI agent or search service not available in node")
    
    return True


def main():
    """Run all integration tests."""
    print("Web Search Integration Tests")
    print("=" * 80)
    
    # Check environment
    print("\nEnvironment Check:")
    print(f"  SERPAPI_API_KEY: {'Set' if os.getenv('SERPAPI_API_KEY') else 'Not set'}")
    print(f"  WEB_SEARCH_ENABLED: {os.getenv('WEB_SEARCH_ENABLED', 'true')}")
    print(f"  DOC_GENERATION_MODE: {os.getenv('DOC_GENERATION_MODE', 'ai_assisted')}")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    try:
        if test_search_service_standalone():
            tests_passed += 1
    except Exception as e:
        print(f"\n✗ Search service test failed: {e}")
    
    try:
        if test_document_ai_agent_integration():
            tests_passed += 1
    except Exception as e:
        print(f"\n✗ DocumentAiAgent integration test failed: {e}")
    
    try:
        if test_node_integration():
            tests_passed += 1
    except Exception as e:
        print(f"\n✗ Node integration test failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"Integration Tests Complete: {tests_passed}/{total_tests} passed")
    
    if tests_passed < total_tests:
        print("\n⚠️  Some tests failed. Check your configuration:")
        print("  1. Ensure SERPAPI_API_KEY is set in .env file")
        print("  2. Ensure WEB_SEARCH_ENABLED=true in .env file")
        print("  3. Install dependencies: pip install google-search-results")
    else:
        print("\n✅ All integration tests passed!")


if __name__ == "__main__":
    main()