#!/usr/bin/env python3
"""Test AI configuration loading."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment Variables Check:")
print(f"DOC_GENERATION_MODE: {os.getenv('DOC_GENERATION_MODE', 'Not set')}")
print(f"GEMINI_API_KEY: {'Present' if os.getenv('GEMINI_API_KEY') else 'Not set'}")
print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'Not set')}")
print(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'Not set')}")
print(f"LLM_TEMPERATURE: {os.getenv('LLM_TEMPERATURE', 'Not set')}")
print(f"LLM_MAX_TOKENS: {os.getenv('LLM_MAX_TOKENS', 'Not set')}")

# Check if AI should be enabled
mode = os.getenv('DOC_GENERATION_MODE', 'ai_assisted')
enabled = mode == 'ai_assisted'
print(f"\nAI Status:")
print(f"Mode: {mode}")
print(f"Should be enabled: {enabled}")