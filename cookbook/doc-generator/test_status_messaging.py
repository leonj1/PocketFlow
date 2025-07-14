#!/usr/bin/env python3
"""
Test script to demonstrate improved status messaging in document generation.
This simulates different scenarios to show how the system reports status.
"""

import sys
sys.path.append('/app/cookbook/doc-generator')

def simulate_low_score_scenario():
    """Simulate a document with low completeness score"""
    print("\n" + "="*80)
    print("SCENARIO 1: Low Completeness Score (30/100)")
    print("="*80)
    
    # Simulate shared state after low score
    shared = {
        "document_published": False,
        "rejection_reason": "Completeness score too low (30/100)",
        "completeness_analysis": {
            "overall_completeness": 30.0,
            "readability_issues": [1, 2, 3],  # 3 issues
            "conceptual_gaps": [1, 2, 3, 4, 5],  # 5 issues
            "unfulfilled_goals": [1, 2],  # 2 issues
            "scope_violations": [1]  # 1 issue
        },
        "attempts": {"current": 3, "max": 3},
        "sections": {
            "Executive Summary": {"word_count": 329, "status": "completed", "quality_score": 8},
            "Problem Statement": {"word_count": 324, "status": "completed", "quality_score": 8},
            "Chosen Solution": {"word_count": 415, "status": "completed", "quality_score": 8},
        }
    }
    
    # Simulate what AbandonNode would print
    print("\n⚠️  DOCUMENT GENERATION ABANDONED")
    print("="*60)
    print(f"\n❌ Reason: Maximum attempts reached ({shared['attempts']['current']}/{shared['attempts']['max']})")
    print(f"❌ Final Completeness Score: {shared['completeness_analysis']['overall_completeness']}/100 (Required: 70/100)")
    print(f"\n📋 Outstanding Issues:")
    print(f"   - 3 readability issues")
    print(f"   - 5 conceptual gaps")
    print(f"   - 2 unfulfilled goals")
    print(f"   - 1 scope violations")
    
    # Simulate what EndNode would print
    print("\n" + "="*60)
    print("DOCUMENT GENERATION SUMMARY")
    print("="*60)
    print("❌ Document Status: NOT PUBLISHED")
    print(f"❓ Reason: {shared['rejection_reason']}")
    print(f"\n❌ Completeness Score: 30.0/100")
    print(f"   (Minimum required: 70/100)")
    print(f"\n🔄 Revision Attempts: 3/3")
    print("\n📝 Section Summary:")
    print("   ✅ Executive Summary: 329 words, Quality: 8/10")
    print("   ✅ Problem Statement: 324 words, Quality: 8/10")
    print("   ✅ Chosen Solution: 415 words, Quality: 8/10")
    print("\n" + "="*60)
    print("❌ Document generation ended without publishing.")
    print("   Review the issues above and try again.")
    print("="*60)

def simulate_successful_scenario():
    """Simulate a successfully published document"""
    print("\n" + "="*80)
    print("SCENARIO 2: Successful Publication (85/100)")
    print("="*80)
    
    shared = {
        "document_published": True,
        "output_filename": "output/adr-001.md",
        "completeness_analysis": {"overall_completeness": 85.0},
        "attempts": {"current": 1, "max": 3},
        "document": "Full document content here...",
        "sections": {
            "Executive Summary": {"word_count": 350, "status": "completed", "quality_score": 9},
            "Problem Statement": {"word_count": 400, "status": "completed", "quality_score": 9},
        }
    }
    
    # Simulate what EndNode would print
    print("\n" + "="*60)
    print("DOCUMENT GENERATION SUMMARY")
    print("="*60)
    print("✅ Document Status: PUBLISHED")
    print(f"📁 Output Location: {shared['output_filename']}")
    print(f"\n✅ Completeness Score: 85.0/100")
    print(f"\n🔄 Revision Attempts: 1/3")
    print(f"\n📊 Document Statistics:")
    print(f"   Total Word Count: 4200")
    print("\n📝 Section Summary:")
    print("   ✅ Executive Summary: 350 words, Quality: 9/10")
    print("   ✅ Problem Statement: 400 words, Quality: 9/10")
    print("\n" + "="*60)
    print("✅ Document generation completed successfully!")
    print("="*60)

def simulate_committee_rejection():
    """Simulate committee rejection"""
    print("\n" + "="*80)
    print("SCENARIO 3: Committee Rejection (75/100 but rejected)")
    print("="*80)
    
    shared = {
        "document_published": False,
        "rejection_reason": "Rejected by committee review",
        "completeness_analysis": {"overall_completeness": 75.0},
        "attempts": {"current": 2, "max": 3},
    }
    
    print("\n" + "="*60)
    print("DOCUMENT GENERATION SUMMARY")
    print("="*60)
    print("❌ Document Status: NOT PUBLISHED")
    print(f"❓ Reason: {shared['rejection_reason']}")
    print(f"\n✅ Completeness Score: 75.0/100")
    print(f"\n🔄 Revision Attempts: 2/3")
    print("\n" + "="*60)
    print("❌ Document generation ended without publishing.")
    print("   Review the issues above and try again.")
    print("="*60)

def main():
    """Run all test scenarios"""
    print("\nDOCUMENT STATUS MESSAGING TEST")
    print("This demonstrates how the improved messaging shows document status\n")
    
    # Run scenarios
    simulate_low_score_scenario()
    simulate_successful_scenario()
    simulate_committee_rejection()
    
    print("\n" + "="*80)
    print("KEY IMPROVEMENTS:")
    print("="*80)
    print("1. Clear indication of whether document was published")
    print("2. Specific reason why document wasn't published")
    print("3. Completeness score with threshold reminder")
    print("4. Number of revision attempts")
    print("5. Detailed breakdown of issues for failed documents")
    print("6. Helpful suggestions for improvement")
    print("\nUsers will now clearly understand why their output folder might be empty!")

if __name__ == "__main__":
    main()