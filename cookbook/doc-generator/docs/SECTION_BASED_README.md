# Section-Based Document Generator

## Overview

The section-based document generator is an enhanced version of the original document generator that processes document sections individually rather than the entire document at once. This approach provides several key advantages:

- **Granular Processing**: Each section is generated and reviewed independently
- **Parallel Execution**: Multiple sections can be processed simultaneously  
- **Efficient Revisions**: Changes to one section don't require regenerating the entire document
- **Better Context Management**: LLMs work with smaller, focused contexts
- **Section-Specific Expertise**: Different reviewers can focus on their areas of expertise

## Architecture

### Core Components

#### 1. SectionData Structure
Holds all information about a document section:
- Name, target audience, max pages
- Content and current status
- Section-specific feedback
- Quality scores from reviewers
- Version tracking

#### 2. SectionCoordinatorNode
- Initializes section data structures
- Identifies sections ready for processing
- Manages dependencies between sections
- Prevents content duplication

#### 3. SectionDraftingNode (Async)
- Drafts individual sections with awareness of other sections
- Receives context about completed sections to avoid duplication
- Extracts key points for cross-referencing
- Updates section status and metadata

#### 4. SectionReviewNode (Async)
- Reviews sections for quality and consistency
- Provides section-specific feedback
- Assigns quality scores
- Determines if revision is needed

#### 5. DocumentAssemblerNode
- Combines all completed sections
- Ensures proper document structure
- Adds metadata and statistics
- Creates the final document

#### 6. ParallelSectionFlow
- Manages concurrent processing of multiple sections
- Handles up to 3 sections in parallel
- Coordinates async execution

### Enhanced Committee Review

The `AsyncSectionReviewNode` base class enables:
- Reviewers focused on specific sections
- Section-level quality scores and feedback
- Expertise-based section assignment
- Detailed tracking of reviewer opinions

Specialized reviewers include:
- **Security Section Expert**: Authentication, Authorization, Security Checklist
- **Architecture Section Expert**: Core Principles, Implementation, Appendices  
- **Product Section Expert**: Executive Summary, Examples, Checklist

## Workflow

1. **Initialization**: Context loaded, section structures created
2. **Coordination**: Identify sections ready for drafting
3. **Parallel Drafting**: Generate multiple sections concurrently
4. **Section Review**: Individual quality assessment
5. **Assembly**: Combine sections into document
6. **Committee Review**: Section-aware expert evaluation
7. **Revision**: Target specific sections needing work
8. **Publication**: Save document and metadata

## Key Information Flow

### What Each Section Node Knows:

1. **Its Own Context**:
   - Section name and configuration
   - Target audience
   - Page/word limits

2. **Other Sections**:
   - List of all sections and their status
   - Summaries of completed sections
   - Key points from each section

3. **Document Context**:
   - Overall topic and purpose
   - Terminology and definitions
   - Writing style guidelines

4. **Feedback**:
   - Section-specific reviewer comments
   - Quality scores
   - Required changes

## Usage

Run the section-based generator:

```bash
python section_main.py
```

The generator will:
1. Process sections individually
2. Run up to 3 sections in parallel
3. Review each section separately
4. Assemble the final document
5. Save output with metadata

## Benefits Over Monolithic Approach

1. **Efficiency**: 
   - Smaller LLM contexts = faster processing
   - Parallel execution = reduced total time
   - Targeted revisions = less regeneration

2. **Quality**:
   - Focused generation per section
   - Section-specific expert reviews
   - Better consistency tracking

3. **Flexibility**:
   - Easy to add/remove sections
   - Can process sections in any order
   - Dependencies explicitly managed

4. **Traceability**:
   - Version tracking per section
   - Detailed reviewer feedback
   - Quality metrics at section level

## Example Output Structure

```
output/
├── adr-001.md              # Final assembled document
└── adr-001_metadata.yaml   # Section-level metadata
```

The metadata includes:
- Word count per section
- Quality scores
- Version numbers
- Reviewer feedback