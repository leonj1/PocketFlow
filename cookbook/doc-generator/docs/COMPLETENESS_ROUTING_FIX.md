# Document Completeness Routing Fix

## Problem
Documents with low completeness scores (e.g., 30/100) were being published instead of going through revision cycles. The workflow was bypassing the revision process and proceeding directly to committee approval.

## Root Cause
The `DocumentCompletenessNode` had conflicting workflow connections:
1. A default connection: `document_completeness_node >> completeness_report_node`
2. A conditional connection: `document_completeness_node - "needs_improvement" >> section_revision_node`

When the node returned `"needs_improvement"` for low scores, PocketFlow was still following the default path to the report generation, allowing documents to bypass revision.

## Solution

### 1. Explicit Action Returns
Modified `DocumentCompletenessNode` to return explicit actions:
```python
if exec_res["overall_completeness"] < 70:
    print(f"\n  Document needs improvement - triggering revision cycle")
    return "needs_improvement"
else:
    print(f"\n  Document meets completeness threshold - generating report")
    return "generate_report"
```

### 2. Removed Default Connection
Removed the problematic default connection in `flows/completeness.py`:
```python
# Before (problematic):
document_completeness_node >> completeness_report_node

# After (fixed):
# Connections defined in main.py with explicit routing
```

### 3. Explicit Workflow Routing
Updated workflow connections in `main.py` to use only explicit routing:
```python
# No default path - must explicitly route based on score
document_completeness_node - "generate_report" >> completeness_report_node  # Score >= 70
document_completeness_node - "needs_improvement" >> section_revision_node   # Score < 70
```

## Expected Behavior

### For Low-Scoring Documents (< 70%):
1. Document assembled from sections
2. Completeness analysis runs → Score: 30/100
3. Node returns `"needs_improvement"`
4. Flow routes to `section_revision_node`
5. Feedback distributed to sections
6. Sections marked for revision
7. Loop back to reprocess sections
8. Continue until score >= 70% or max attempts reached

### For High-Scoring Documents (>= 70%):
1. Document assembled from sections
2. Completeness analysis runs → Score: 85/100
3. Node returns `"generate_report"`
4. Flow routes to `completeness_report_node`
5. Report generated
6. Committee review
7. Publish if approved

## Benefits
1. **No Bypass**: Low-quality documents cannot skip to committee
2. **Guaranteed Quality**: Documents must meet 70% threshold
3. **Clear Routing**: Explicit actions make flow debugging easier
4. **Iterative Improvement**: Documents improve through revision cycles

The fix ensures that a document scoring 30/100 will go through multiple revision iterations until it either:
- Achieves a score >= 70/100
- Reaches the maximum attempt limit (3 attempts)