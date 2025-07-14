# Document Completeness Loop Fix

## Problem
With a completeness score of 28.3/100, the document should have been sent back to the working group (section revision) for improvement, but instead the flow terminated with an error:
```
Flow ends: 'needs_improvement' not found in ['default']
```

## Root Cause
The `DocumentCompletenessNode` correctly returned "needs_improvement" for the low score, but this action had no connection in the workflow graph.

## Solution

### 1. Added Direct Connection
```python
# Document completeness analysis routes based on score
document_completeness_node >> completeness_report_node  # Default path (score >= 70)
document_completeness_node - "needs_improvement" >> section_revision_node  # Low score path
```

### 2. Removed Redundant Gate
- Eliminated `CompletenessGateNode` since `DocumentCompletenessNode` already performs the gating
- Simplified flow by having one decision point

### 3. Enhanced Tracking
- Document completeness node now increments attempt counter
- Shows current attempt number when triggering revisions

## Updated Flow

```
Document Assembly
       ↓
Document Completeness Analysis
       ↓
   Score < 70?
   Yes ↓        No ↓
Section Revision   Completeness Report
       ↓                    ↓
   (Loop back)        Committee Review
                            ↓
                        Publish/Reject
```

## Expected Behavior

When a document scores low (e.g., 28.3/100):

1. **Immediate Revision**: Document goes to `SectionRevisionNode`
2. **Feedback Distribution**: Completeness issues converted to section-specific feedback
3. **Section Updates**: Sections marked for revision based on:
   - Readability issues
   - Conceptual gaps
   - Unfulfilled goals
   - Scope violations
4. **Reprocessing**: Sections redrafted with feedback
5. **Reassembly**: Updated sections assembled into new document
6. **Re-evaluation**: Completeness checked again
7. **Iteration**: Process repeats until score ≥ 70% or max attempts reached

## Benefits

1. **Quality Assurance**: Documents must meet 70% completeness threshold
2. **Targeted Improvements**: Specific feedback guides revisions
3. **Iterative Enhancement**: Multiple revision cycles allowed
4. **No Premature Termination**: Low-quality documents improved rather than abandoned

The working group (section revision process) now properly iterates on documents until they meet quality standards.