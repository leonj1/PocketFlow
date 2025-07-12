#!/usr/bin/env python3
"""
Test script for AI integration in document workflow
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ai_agent import AiAgent, get_default_agent
from document_ai_agents import DocumentAiAgent, get_document_ai_agent
from document_workflow import DocumentWorkflow


def test_ai_agent_initialization():
    """Test basic AI agent initialization."""
    print("Testing AI Agent Initialization")
    print("================================\n")
    
    # Check environment
    api_key_set = bool(os.getenv('GEMINI_API_KEY'))
    print(f"1. Environment Check:")
    print(f"   GEMINI_API_KEY set: {api_key_set}")
    print(f"   LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'not set')}")
    print(f"   LLM_MODEL: {os.getenv('LLM_MODEL', 'not set')}")
    
    if not api_key_set:
        print("\n⚠️  Warning: GEMINI_API_KEY not set in environment")
        print("   Copy .env.example to .env and add your API key")
        print("   AI features will be disabled")
    
    # Test initialization
    print("\n2. Testing AiAgent initialization...")
    try:
        agent = get_default_agent()
        config = agent.get_config()
        
        print("✓ AI Agent initialized successfully")
        print(f"   Provider: {config['provider']}")
        print(f"   Model: {config['model']}")
        print(f"   Enabled: {config['enabled']}")
        
        if config['enabled']:
            # Test basic invocation
            print("\n3. Testing basic AI invocation...")
            response = agent.invoke("Say 'Hello from PocketFlow AI' in exactly 5 words")
            print(f"   Response: {response}")
    
    except Exception as e:
        print(f"✗ AI Agent initialization failed: {e}")
    
    # Test DocumentAiAgent
    print("\n4. Testing DocumentAiAgent...")
    try:
        doc_agent = get_document_ai_agent()
        print("✓ DocumentAiAgent initialized")
        
        if doc_agent.is_enabled():
            # Test needs assessment
            test_context = {
                "topic": "Test Document",
                "purpose": "Testing AI integration",
                "audience": {"primary": [{"role": "Developers"}]},
                "scope": {"includes": ["AI features", "Integration testing"]}
            }
            
            print("\n5. Testing AI needs assessment...")
            needs = doc_agent.assess_needs(test_context)
            print(f"✓ Identified {len(needs.identified_needs)} needs")
            print(f"   First need: {needs.identified_needs[0] if needs.identified_needs else 'None'}")
            
    except Exception as e:
        print(f"✗ DocumentAiAgent test failed: {e}")


def test_workflow_with_ai():
    """Test the document workflow with AI features."""
    print("\n\nTesting Document Workflow with AI")
    print("=================================\n")
    
    # Check if context.yml exists
    if not Path("context.yml").exists():
        print("✗ context.yml not found")
        return
    
    print("The full workflow requires user interaction.")
    print("AI features will be used if GEMINI_API_KEY is set.\n")
    
    print("To test the full workflow:")
    print("1. Ensure GEMINI_API_KEY is set in .env")
    print("2. Run: python3 document_workflow.py")
    print("3. Observe AI-generated content and reviews")
    
    # Show what features are available
    agent = get_default_agent()
    if agent.is_enabled():
        print("\n✅ AI Features Available:")
        print("   - AI-powered needs assessment")
        print("   - Intelligent outline generation")
        print("   - AI content generation for sections")
        print("   - AI document review and feedback")
    else:
        print("\n⚠️  AI Features Disabled (no API key)")
        print("   The workflow will use placeholder content")


def test_ai_modes():
    """Test different AI modes and configurations."""
    print("\n\nTesting AI Modes")
    print("================\n")
    
    # Test environment variables
    modes = {
        "DOC_GENERATION_MODE": os.getenv('DOC_GENERATION_MODE', 'not set'),
        "AI_REVIEW_ENABLED": os.getenv('AI_REVIEW_ENABLED', 'not set'),
        "AI_SUGGESTION_MODE": os.getenv('AI_SUGGESTION_MODE', 'not set')
    }
    
    print("Current AI Configuration:")
    for key, value in modes.items():
        print(f"  {key}: {value}")
    
    print("\nAvailable modes:")
    print("  DOC_GENERATION_MODE: ai_assisted | human_only")
    print("  AI_REVIEW_ENABLED: true | false")
    print("  AI_SUGGESTION_MODE: true | false")


if __name__ == "__main__":
    print("PocketFlow AI Integration Test")
    print("==============================\n")
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    test_ai_agent_initialization()
    test_workflow_with_ai()
    test_ai_modes()
    
    print("\n✅ AI integration tests completed!")
    print("\nNote: For full integration testing, run the document workflow")
    print("with a valid GEMINI_API_KEY set in your .env file.")