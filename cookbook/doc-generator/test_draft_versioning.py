#!/usr/bin/env python3
"""
Test script to demonstrate the draft versioning system.
This simulates saving multiple document versions.
"""

import os
import yaml
from datetime import datetime

def test_draft_versioning():
    """Simulate the draft versioning process"""
    print("\nDRAFT VERSIONING SYSTEM TEST")
    print("="*60)
    
    # Simulate session data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"test_doc_session_{timestamp}"
    
    print(f"\n📝 Starting new session: {session_id}")
    
    # Simulate three attempts with improving scores
    attempts = [
        {"score": 30, "issues": {"readability": 3, "gaps": 5, "goals": 2, "scope": 1}},
        {"score": 45, "issues": {"readability": 2, "gaps": 3, "goals": 1, "scope": 1}},
        {"score": 60, "issues": {"readability": 1, "gaps": 2, "goals": 1, "scope": 0}},
    ]
    
    versions = []
    
    for i, attempt in enumerate(attempts, 1):
        print(f"\n🔄 Attempt {i}:")
        
        # Create directory
        base_dir = f"drafts/{session_id}/attempt_{i}"
        os.makedirs(base_dir, exist_ok=True)
        
        # Save mock document
        doc_path = f"{base_dir}/document_v{i}.md"
        with open(doc_path, "w") as f:
            f.write(f"# Test Document - Version {i}\n\n")
            f.write(f"This is version {i} of the document.\n")
            f.write(f"Completeness Score: {attempt['score']}/100\n")
        
        # Save mock completeness analysis
        comp_path = f"{base_dir}/completeness_v{i}.md"
        with open(comp_path, "w") as f:
            f.write(f"# Completeness Analysis - Attempt {i}\n\n")
            f.write(f"**Overall Score:** {attempt['score']}/100\n\n")
            f.write("## Issues Summary\n\n")
            f.write(f"- Readability Issues: {attempt['issues']['readability']}\n")
            f.write(f"- Conceptual Gaps: {attempt['issues']['gaps']}\n")
            f.write(f"- Unfulfilled Goals: {attempt['issues']['goals']}\n")
            f.write(f"- Scope Violations: {attempt['issues']['scope']}\n")
        
        # Save mock sections data
        sections_path = f"{base_dir}/sections_v{i}.yaml"
        sections_data = {
            "Executive Summary": {
                "status": "completed",
                "word_count": 300 + i * 50,
                "quality_score": 7 + i * 0.5,
                "version": i
            }
        }
        with open(sections_path, "w") as f:
            yaml.dump(sections_data, f)
        
        print(f"   ✅ Saved draft version {i} to: {base_dir}")
        print(f"   📊 Completeness Score: {attempt['score']}/100")
        
        versions.append({
            "attempt": i,
            "path": base_dir,
            "score": attempt['score']
        })
    
    # Create session summary
    summary_path = f"drafts/{session_id}/summary.md"
    with open(summary_path, "w") as f:
        f.write("# Document Generation Session Summary\n\n")
        f.write(f"**Session ID:** {session_id}\n")
        f.write(f"**Total Attempts:** {len(attempts)}\n\n")
        f.write("## Score Progression\n\n")
        for v in versions:
            f.write(f"- Attempt {v['attempt']}: {v['score']}/100\n")
        f.write("\n## Final Status\n\n")
        f.write("❌ Document was not published\n")
        f.write("❓ Reason: Completeness score too low (60/100)\n")
        f.write("\n## Next Steps\n\n")
        f.write("1. Review the completeness analysis in attempt_3\n")
        f.write("2. Edit document_v3.md to address remaining issues\n")
        f.write("3. Focus on conceptual gaps and unfulfilled goals\n")
    
    print(f"\n📄 Created session summary: {summary_path}")
    
    # Show final output
    print("\n" + "="*60)
    print("FINAL OUTPUT (as shown to user):")
    print("="*60)
    print("\n📁 Draft Versions Saved:")
    for v in versions:
        print(f"   - Attempt {v['attempt']}: {v['path']} (Score: {v['score']}/100)")
    
    print(f"\n💡 All draft versions saved in: drafts/{session_id}/")
    print("   You can manually edit the latest draft to address the issues.")
    
    # Show directory structure
    print("\n📂 Created Directory Structure:")
    for root, dirs, files in os.walk(f"drafts/{session_id}"):
        level = root.replace(f"drafts/{session_id}", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    test_draft_versioning()