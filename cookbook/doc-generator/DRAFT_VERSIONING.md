# Document Draft Versioning System

## Overview
The document generator now saves every version of your document throughout the generation process, ensuring no work is ever lost. Even if a document fails quality checks, all drafts are preserved for review and manual editing.

## How It Works

### 1. Automatic Version Saving
After each document assembly, the system automatically saves:
- The complete document draft
- Completeness analysis with score and issues
- Section metadata (status, quality scores, feedback)
- Revision feedback for each section

### 2. Directory Structure
```
drafts/
└── adr-001_session_20240115_143022/
    ├── attempt_1/
    │   ├── document_v1.md          # First draft
    │   ├── completeness_v1.md      # Score: 30/100
    │   ├── sections_v1.yaml        # Section details
    │   └── feedback_v1.yaml        # Revision feedback
    ├── attempt_2/
    │   ├── document_v2.md          # Second draft
    │   ├── completeness_v2.md      # Score: 45/100
    │   ├── sections_v2.yaml
    │   └── feedback_v2.yaml
    ├── attempt_3/
    │   ├── document_v3.md          # Final draft
    │   ├── completeness_v3.md      # Score: 60/100
    │   ├── sections_v3.yaml
    │   └── feedback_v3.yaml
    └── summary.md                  # Session overview
```

### 3. Session Summary
Each session includes a `summary.md` file containing:
- Session ID and start time
- Score progression across attempts
- Final publication status
- Outstanding issues
- Next steps for improvement

## Benefits

### Never Lose Work
- Every iteration is saved, even if generation fails
- Can recover from any point in the process
- Manual editing possible on any draft

### Learning Tool
- See how the document evolved
- Understand which revisions improved scores
- Learn from the AI's feedback

### Debugging Aid
- Complete audit trail of changes
- Track which feedback was addressed
- Identify patterns in improvements

### Transparency
- Full visibility into AI's work
- See exactly what changes were made
- Understand reasoning behind revisions

## Example Output

When generation completes (successfully or not), you'll see:

```
📁 Draft Versions Saved:
   - Attempt 1: drafts/adr-001_session_20240115_143022/attempt_1 (Score: 30/100)
   - Attempt 2: drafts/adr-001_session_20240115_143022/attempt_2 (Score: 45/100)
   - Attempt 3: drafts/adr-001_session_20240115_143022/attempt_3 (Score: 60/100)

💡 All draft versions saved in: drafts/adr-001_session_20240115_143022/
   You can manually edit the latest draft to address the issues.
```

## Working with Drafts

### Option 1: Manual Editing
1. Navigate to the latest attempt folder
2. Open `document_vX.md` in your editor
3. Review `completeness_vX.md` for specific issues
4. Make manual improvements based on feedback
5. Use the edited document as your final version

### Option 2: Learning from Feedback
1. Open `feedback_vX.yaml` to see section-specific feedback
2. Review what the AI tried to improve
3. Use insights for future document creation

### Option 3: Cherry-Pick Best Sections
1. Compare sections across different attempts
2. Take the best version of each section
3. Manually assemble an optimal document

## Implementation Details

### DraftVersioningNode
- Triggered after DocumentAssemblerNode
- Creates session tracking on first run
- Saves all relevant data for each attempt
- Updates session version list

### Enhanced Status Messages
- EndNode shows all saved draft locations
- Includes scores for each version
- Creates session summary automatically
- Provides clear next steps

### No Performance Impact
- Saves happen asynchronously
- Minimal overhead (< 100ms per save)
- Only saves when document is assembled
- Efficient YAML/Markdown formats

## Future Enhancements

### Planned Features
- Diff generation between versions
- Visual score progression charts
- Automatic best-section selection
- Compression for old sessions

### Configuration Options
```yaml
draft_settings:
  save_all_versions: true
  save_on_success: true
  include_diffs: false
  compress_old_versions: false
  retention_days: 30
```

With this system, you'll never lose work again, and every document generation session becomes a learning opportunity!