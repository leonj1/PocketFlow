#!/usr/bin/env python3
"""
Test script to demonstrate the resume detection feature.
Creates mock documents and sessions to show how resume works.
"""

import os
import yaml
from datetime import datetime, timedelta

def create_mock_published_document():
    """Create a mock published document"""
    os.makedirs("output", exist_ok=True)
    
    content = """# ADR to prevent OAuth JWT token reuse

**Document Type:** Technical Standard
**Version:** 1.0

## Executive Summary

This document outlines security standards for preventing JWT token reuse across API services without user consent.

## Problem Statement

APIs face security challenges when JWT tokens issued for one service are reused by other services without explicit user consent. This creates security vulnerabilities and privacy concerns.

## Considered Solutions

We evaluated three approaches:
1. Token binding to specific services
2. Consent-based token sharing
3. Service-specific token generation

## Chosen Solution

Implement consent-based token sharing with service binding to ensure tokens can only be used by explicitly authorized services.

## Rationale for Chosen Solution

This approach balances security with usability while maintaining user control over token usage.

## Steps for Tracking Adoption and Adherance

1. Implement token service registry
2. Add consent UI components
3. Monitor token usage patterns
4. Generate compliance reports

## Mermaid Diagram Example

```mermaid
graph TD
    A[User] --> B[Service A]
    B --> C{Consent Check}
    C -->|Approved| D[Service B]
    C -->|Denied| E[Access Denied]
```

## Python Code Example

```python
def validate_token_consent(token, target_service):
    claims = decode_jwt(token)
    allowed_services = claims.get('consented_services', [])
    return target_service in allowed_services
```

## Risks and Mitigations

- Risk: Token theft - Mitigation: Short expiry times
- Risk: Consent fatigue - Mitigation: Smart consent grouping

## Appendices

Additional implementation details and references.
"""
    
    with open("output/adr-001.md", "w") as f:
        f.write(content)
    
    # Set modification time to 30 minutes ago
    mod_time = datetime.now() - timedelta(minutes=30)
    os.utime("output/adr-001.md", (mod_time.timestamp(), mod_time.timestamp()))
    
    print("✅ Created mock published document: output/adr-001.md")

def create_mock_draft_session():
    """Create a mock draft session with multiple attempts"""
    session_id = "adr-001_session_20240115_140000"
    
    # Create 3 attempts with improving scores
    for attempt in range(1, 4):
        attempt_dir = f"drafts/{session_id}/attempt_{attempt}"
        os.makedirs(attempt_dir, exist_ok=True)
        
        # Create document
        doc_content = f"""# ADR Draft - Attempt {attempt}

This is attempt {attempt} of the document.
Score: {30 + attempt * 15}/100
"""
        with open(f"{attempt_dir}/document_v{attempt}.md", "w") as f:
            f.write(doc_content)
        
        # Create completeness analysis
        score = 30 + attempt * 15
        with open(f"{attempt_dir}/completeness_v{attempt}.md", "w") as f:
            f.write(f"# Completeness Analysis - Attempt {attempt}\n\n")
            f.write(f"**Overall Score:** {score}/100\n\n")
            f.write(f"## Issues Summary\n\n")
            f.write(f"- Readability Issues: {5 - attempt}\n")
            f.write(f"- Conceptual Gaps: {7 - attempt * 2}\n")
        
        # Create sections metadata
        sections_data = {
            "Executive Summary": {
                "status": "completed",
                "word_count": 100 + attempt * 50,
                "quality_score": 6 + attempt,
                "version": attempt
            },
            "Problem Statement": {
                "status": "completed",
                "word_count": 150 + attempt * 30,
                "quality_score": 7 + attempt * 0.5,
                "version": attempt
            }
        }
        with open(f"{attempt_dir}/sections_v{attempt}.yaml", "w") as f:
            yaml.dump(sections_data, f)
    
    # Create summary
    with open(f"drafts/{session_id}/summary.md", "w") as f:
        f.write(f"# Document Generation Session Summary\n\n")
        f.write(f"**Session ID:** {session_id}\n")
        f.write(f"**Total Attempts:** 3\n\n")
        f.write("## Score Progression\n\n")
        f.write("- Attempt 1: 45/100\n")
        f.write("- Attempt 2: 60/100\n")
        f.write("- Attempt 3: 75/100\n")
    
    # Set modification time to 45 minutes ago
    mod_time = datetime.now() - timedelta(minutes=45)
    for root, dirs, files in os.walk(f"drafts/{session_id}"):
        for file in files:
            filepath = os.path.join(root, file)
            os.utime(filepath, (mod_time.timestamp(), mod_time.timestamp()))
    
    print(f"✅ Created mock draft session: drafts/{session_id}")

def test_resume_detection():
    """Test the resume detection logic"""
    print("\nRESUME DETECTION FEATURE TEST")
    print("="*60)
    
    # Create mock data
    create_mock_published_document()
    create_mock_draft_session()
    
    print("\n" + "-"*60)
    print("Simulating Resume Detection:")
    print("-"*60)
    
    # Simulate what ResumeDetectorNode would show
    print("\n🔍 Resume Detection Node\n")
    print("📂 Found existing work:\n")
    
    print("1. Published document: output/adr-001.md")
    print("   - Last modified: 30 minutes ago")
    print("   - Completeness: Unknown (needs analysis)")
    print()
    
    print("2. Draft session: adr-001_session_20240115_140000")
    print("   - Last modified: 45 minutes ago")
    print("   - Attempts made: 3")
    print("   - Best score: 75/100")
    print()
    
    print("3. Start fresh (ignore existing work)")
    print()
    
    print("⚡ Auto-selecting most recent work (option 1)")
    print()
    
    # Show what happens when loading published document
    print("-"*60)
    print("Loading Published Document:")
    print("-"*60)
    print("\n📄 Loading published document: output/adr-001.md")
    print("✅ Document loaded and parsed into sections.")
    print("📝 Found 10 sections")
    print("\nNext: Document will be analyzed for completeness")
    print("      If score < 70%, revision cycle will begin")
    print("      If score >= 70%, can still choose to improve")
    
    # Show what happens when loading draft
    print("\n" + "-"*60)
    print("Alternative: Loading Draft Session:")
    print("-"*60)
    print("\n📁 Loading draft session: adr-001_session_20240115_140000")
    print("✅ Loaded document from attempt 3")
    print("✅ Loaded section metadata")
    print("✅ Loaded completeness analysis")
    print("✅ Resuming from attempt 3/3")
    print("\n⚠️  Warning: Already at maximum attempts!")
    print("\nNext: Will continue from exact stopping point")
    print("      Can extend beyond max attempts if needed")

def cleanup():
    """Clean up test files"""
    import shutil
    if os.path.exists("output/adr-001.md"):
        os.remove("output/adr-001.md")
    if os.path.exists("drafts/adr-001_session_20240115_140000"):
        shutil.rmtree("drafts/adr-001_session_20240115_140000")
    print("\n✅ Cleaned up test files")

if __name__ == "__main__":
    test_resume_detection()
    cleanup()