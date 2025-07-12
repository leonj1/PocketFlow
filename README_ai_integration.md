# AI Integration for PocketFlow Document Workflow

This document describes the AI integration added to the PocketFlow document workflow using Google Gemini and PydanticAI.

## Overview

The document workflow now includes AI-powered features for:
- 🤖 Intelligent needs assessment
- 📋 AI-powered outline generation  
- ✍️ Automated content generation for document sections
- 🔍 AI document review and feedback
- 💡 AI suggestions for approval decisions

## Configuration

### 1. Set Up Environment

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Google Gemini Configuration
GEMINI_API_KEY=your-actual-api-key-here
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp

# AI Feature Toggles
DOC_GENERATION_MODE=ai_assisted  # or human_only
AI_REVIEW_ENABLED=true
AI_SUGGESTION_MODE=true
```

### 2. Get a Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## Architecture

### AI Agent Service (`ai_agent.py`)

Base service class that:
- Manages LLM connections using PydanticAI
- Handles API key and configuration
- Provides sync/async invocation methods
- Supports multiple LLM providers (currently Google Gemini)

### Document AI Agents (`document_ai_agents.py`)

Specialized agents with structured outputs:
- `DocumentSection`: Schema for AI-generated sections
- `ReviewFeedback`: Schema for AI review results
- `NeedsAssessment`: Schema for needs analysis
- `DocumentOutline`: Schema for document structure

### Integration Points

1. **NeedsAssessmentNode**
   - Uses AI to analyze context and identify document needs
   - Falls back to defaults if AI is unavailable

2. **OutlineTemplateNode**
   - AI generates intelligent outline based on needs
   - Considers audience, constraints, and deliverables

3. **DocumentDraftingNode**
   - AI generates content for each section
   - Maintains context from previous sections
   - Tracks whether content is AI-generated

4. **PeerReviewNode**
   - AI reviews document before human review
   - Provides structured feedback with confidence scores
   - Shows AI recommendations to human reviewers

## Usage Examples

### Running with AI Enabled (Default)

```bash
# With Docker
docker-compose run --rm document-workflow

# Or directly
python3 document_workflow.py
```

### Running without AI

Set in `.env`:
```env
DOC_GENERATION_MODE=human_only
```

### Testing AI Integration

```bash
python3 test_ai_integration.py
```

## AI Features in Action

### 1. AI Needs Assessment
```
🤖 Running AI needs assessment...

============================================================
AI Needs Assessment
============================================================
Identified Needs:
  • Clear API authentication examples
  • Security vulnerability prevention guides
  • Performance benchmarking tools
  
Priority Areas:
  • Authentication and authorization
  • Input validation strategies
  
Recommended Approach: Phased implementation with security-first design
============================================================
```

### 2. AI Content Generation
```
Drafting section 1: Executive Summary
  Using AI to generate content...
  ✓ AI generated 342 words
```

### 3. AI Document Review
```
🤖 Running AI review...

============================================================
AI Review Results
============================================================
Overall Assessment: Good
Confidence: 85%

Strengths:
  • Comprehensive security coverage
  • Clear examples provided
  • Well-structured content

Issues Found:
  • Missing rate limiting details
  • GraphQL security not addressed

AI Recommendation: REVISE
============================================================
```

## Fallback Behavior

The system gracefully handles AI failures:
- If API key is missing: Uses placeholder content
- If AI generation fails: Falls back to template content
- If AI review fails: Proceeds with manual review only

## Security Considerations

1. **API Keys**: Never commit `.env` files with real API keys
2. **Content Validation**: Human review is always required
3. **Data Privacy**: Document content is sent to Google's API
4. **Rate Limits**: Be aware of Gemini API quotas

## Customization

### Adding New AI Capabilities

1. Create new schema in `document_ai_agents.py`:
```python
class CustomAnalysis(BaseModel):
    findings: List[str]
    recommendations: Dict[str, str]
```

2. Add method to `DocumentAiAgent`:
```python
def analyze_custom(self, content: str) -> CustomAnalysis:
    # Implementation
```

3. Use in workflow nodes:
```python
analysis = self.ai_agent.analyze_custom(content)
```

### Switching LLM Providers

To add OpenAI support:
1. Update `ai_agent.py` to handle `provider='openai'`
2. Add OpenAI model initialization
3. Set `LLM_PROVIDER=openai` in `.env`

## Performance

- Initial AI calls may take 2-5 seconds
- Subsequent calls are faster due to connection reuse
- Content generation scales with section complexity
- Review time depends on document length

## Troubleshooting

### "API token required"
- Ensure `GEMINI_API_KEY` is set in `.env`
- Check the key is valid at Google AI Studio

### "AI generation failed"
- Check API quotas and rate limits
- Verify internet connectivity
- Review error logs for details

### AI content seems generic
- Provide more detailed context in `context.yml`
- Ensure scope and constraints are specific
- Add more examples to the context

## Future Enhancements

1. **Multi-model Support**: Use different models for different tasks
2. **Caching**: Cache AI responses for similar requests
3. **Fine-tuning**: Custom models for specific document types
4. **Streaming**: Real-time content generation display
5. **Embeddings**: Semantic search through document history