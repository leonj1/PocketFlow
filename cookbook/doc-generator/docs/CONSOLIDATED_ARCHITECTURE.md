# Consolidated Document Generator Architecture

## Overview

The document generator has been consolidated into a single `main.py` that always uses the most thorough approach: section-based processing with completeness analysis. This ensures the highest quality output for all documents.

## Architecture Principles

1. **No Compromises on Quality**: Always uses section-level processing
2. **Mandatory Completeness**: Every document undergoes completeness analysis
3. **Single Optimal Workflow**: One path that guarantees the best results
4. **Parallel Processing**: Sections are processed concurrently for efficiency

## Workflow Components

### 1. Section Processing
- **SectionCoordinatorNode**: Manages section dependencies and readiness
- **ParallelSectionNode**: Processes up to 3 sections simultaneously
- **SectionDraftingNode**: Generates individual sections with context awareness
- **SectionCompletenessNode**: Immediate readability checks per section
- **SectionReviewNode**: Quality review for each section

### 2. Completeness Analysis
- **DocumentCompletenessNode**: Comprehensive analysis across dimensions:
  - Readability matching target audience
  - Conceptual coherence and relationships
  - Goal fulfillment tracking
  - Scope compliance checking
- **CompletenessGateNode**: Enforces 70% minimum quality score
- **CompletenessReportNode**: Generates detailed analysis reports

### 3. Committee Review
- **SectionCommitteeNode**: Section-aware expert reviews
- Specialized reviewers for different aspects:
  - Security sections
  - Architecture sections
  - Product/UX sections

## Workflow Sequence

```
1. SectionBasedLeadNode (Start)
   ↓
2. SectionCoordinator → ParallelSectionDrafting
   ↓
3. SectionCompleteness → SectionReview
   ↓ (Loop until all sections complete)
4. DocumentAssembler
   ↓
5. DocumentCompleteness → CompletenessReport → CompletenessGate
   ↓ (Score ≥ 70%)
6. SectionCommittee
   ↓ (Approved)
7. Publisher → End
```

## Key Features

### Always Enabled:
- ✅ Parallel section processing
- ✅ Section-specific word limits
- ✅ Audience-targeted content per section
- ✅ Readability analysis
- ✅ Conceptual gap detection
- ✅ Goal fulfillment verification
- ✅ Scope compliance enforcement
- ✅ Section-aware committee reviews
- ✅ Comprehensive metadata and reports

### Quality Gates:
- Minimum completeness score: 70/100
- Critical issues must be resolved
- Maximum 3 revision attempts
- Committee approval required

## Usage

Simply run:
```bash
python main.py
```

The generator will:
1. Load context from `context.yml`
2. Initialize section structures
3. Process sections in parallel
4. Perform completeness analysis
5. Run committee reviews
6. Save the document and reports

## Output Files

- `output/[filename].md` - The generated document
- `output/[filename]_metadata.yaml` - Section statistics and scores
- `output/[filename]_completeness.md` - Detailed completeness report

## Benefits of Consolidation

1. **Simplicity**: One entry point, one optimal workflow
2. **Quality**: No shortcuts, always the best approach
3. **Consistency**: Every document gets the same thorough treatment
4. **Maintainability**: Single codebase to update and improve
5. **Performance**: Parallel processing built-in

## File Structure

```
main.py                          # Single entry point
context.yml                      # Document configuration
flows/
├── section_based.py            # Section processing nodes
├── section_committee.py        # Section-aware reviews
├── completeness.py             # Completeness analysis
├── working_group.py            # Legacy (kept for compatibility)
├── working_group_complete.py   # Legacy enhanced
├── comittee.py                # Legacy committee
└── committee_complete.py       # Legacy enhanced
```

The legacy files are retained for backward compatibility but are not used in the main workflow.