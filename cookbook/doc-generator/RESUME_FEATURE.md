# Document Resume Feature

## Overview
The document generator now automatically detects existing work and offers to resume from where you left off. This prevents starting from scratch when you already have a document or draft sessions available.

## How It Works

### 1. Automatic Detection
When the generator starts, it checks for:
- **Published documents** in `output/` directory
- **Draft sessions** in `drafts/` directory
- Shows all available options with details

### 2. Resume Options

#### Option A: Resume from Published Document
- Loads existing published document
- Parses it back into sections
- Runs completeness analysis
- If score < 70%, continues improvement
- If score >= 70%, can still improve further

#### Option B: Resume from Draft Session
- Finds most recent draft session
- Loads latest attempt from that session
- Restores all metadata and state
- Continues from where it left off
- Preserves attempt counter

#### Option C: Start Fresh
- Ignores existing work
- Begins new document generation
- Creates new session ID

### 3. User Interface

When existing work is found:
```
🔍 Resume Detection Node

📂 Found existing work:

1. Published document: output/adr-001.md
   - Last modified: 2024-01-15 14:30
   - Completeness: Unknown (needs analysis)

2. Draft session: adr-001_session_20240115_143022
   - Last modified: 2024-01-15 14:25
   - Attempts made: 3
   - Best score: 60/100

3. Start fresh (ignore existing work)

⚡ Auto-selecting most recent work (option 1)
```

## Implementation Details

### Loading Published Documents
1. Reads the markdown file
2. Parses sections based on `## ` headers
3. Matches against expected sections from context.yml
4. Creates section metadata for each found section
5. Marks missing sections as "pending"
6. Proceeds to completeness analysis

### Loading Draft Sessions
1. Finds the session directory
2. Loads latest attempt folder
3. Restores:
   - Document content
   - Section metadata with feedback
   - Completeness analysis results
   - Attempt counter
4. Continues from exact stopping point

### Smart Routing
- If loading existing work → Skip section drafting
- Go directly to document assembly/completeness
- Workflow adapts based on what was loaded

## Benefits

### 1. Iterative Improvement
- Published documents can be enhanced
- Keep improving until perfect
- No need for manual copying

### 2. Crash Recovery
- If generation fails/crashes
- Simply run again
- Automatically continues

### 3. Time Saving
- Don't repeat successful work
- Skip completed sections
- Focus on what needs improvement

### 4. Experimentation
- Try different approaches
- Compare multiple sessions
- Learn from previous attempts

## Example Scenarios

### Scenario 1: Improving Published Document
```
Current: output/adr-001.md exists with unknown score
Action: Load document, analyze completeness
Result: Score is 65/100, needs improvement
Outcome: Continues revision cycle from attempt 1
```

### Scenario 2: Continuing Failed Session
```
Current: Draft session with 3 attempts, best score 60/100
Action: Load attempt 3, check remaining attempts
Result: At max attempts, but can extend
Outcome: Continues from attempt 3 with warning
```

### Scenario 3: Multiple Sessions Available
```
Current: Both published doc and draft sessions exist
Action: Shows all options, auto-selects most recent
Result: User can override or accept suggestion
Outcome: Loads chosen starting point
```

## Configuration Options

Future enhancement - add to context.yml:
```yaml
resume_settings:
  auto_detect: true        # Automatically check for existing work
  prefer_latest: true      # Auto-select most recent
  prompt_user: true        # Ask before resuming
  extend_attempts: true    # Allow exceeding max attempts when resuming
```

## Technical Notes

### Session Continuity
- Preserves session ID when resuming drafts
- Creates new session for fresh starts
- Maintains version history within session

### State Management
- All shared state properly restored
- Attempt counters continue correctly
- Feedback and scores preserved

### Edge Cases Handled
- Missing or corrupted files
- Incomplete sections
- Empty documents
- Max attempts exceeded

## Usage Tips

1. **Always run normally** - Resume detection is automatic
2. **Check the output** - See what was found and loaded
3. **Trust the system** - It preserves all your work
4. **Iterate freely** - You can always improve further

With this feature, you never lose work and can continuously improve documents across multiple sessions!