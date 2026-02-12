# Day 03: AI-Powered Learning Path Generator 🎓

## 📚 What You Will Achieve Today

By the end of Day 3, you will have:

1. ✅ Google Gemini API integration (Flash-Lite, Flash, Pro)
2. ✅ Cascaded AI content generation (Macro → Meso → Micro)
3. ✅ Study plan synthesizer with learning modules
4. ✅ CFU (Check for Understanding) quiz generator
5. ✅ Automatic remediation content creation
6. ✅ Batch API integration for cost optimization (50% savings)
7. ✅ Context caching for repeated prompts (90% savings)
8. ✅ WebSocket progress notifications
9. ✅ Learning asset management

## 🎯 Learning Objectives

### AI Integration
- **Large Language Models**: Work with Google Gemini API
- **Prompt Engineering**: Design effective prompts for content generation
- **Cost Optimization**: Batch API, context caching, model tiering
- **Error Handling**: Graceful degradation, retries, parsing

### Content Generation
- **Cascaded Generation**: Macro (overall plan) → Meso (detailed lessons) → Micro (assets)
- **Structured Output**: Parse JSON from LLM responses
- **Quality Control**: Validate AI-generated content

### Real-Time Communication
- **Django Channels**: WebSocket integration
- **Async Notifications**: Progress updates to frontend
- **Channel Layers**: Redis-based message passing

## 🛠️ Technology Stack (Day 3)

| Technology | Version | Purpose |
|------------|---------|---------|
| Google Generative AI | 0.3.2+ | Gemini API |
| Django Channels | 4.0.0 | WebSocket support |
| channels-redis | 4.1.0 | Channel layer backend |
| Daphne | 4.0.0 | ASGI server |
| Cel | 5.3.4 | Batch job processing |

## 📊 Database Schema (Day 3)

### New Tables
1. **study_plans** - AI-generated learning roadmaps
2. **learning_modules** - High-level modules (Macro tier)
3. **lessons** - Individual lessons (Meso tier)
4. **cfu_quizzes** - Check for Understanding quizzes
5. **cfu_attempts** - User quiz attempts
6. **remediations** - Scaffolded help content
7. **learning_assets** - Curated open-source resources

## ⏱️ Estimated Time: 8 hours

## 🎓 Key Concepts

### 1. Gemini API Model Tiers

**Flash-Lite (Fastest, Cheapest)**
- Simple, structured tasks
- Quiz generation
- Content summarization
- Cost: ~$0.001/1K tokens

**Flash (Balanced)**
- Real-time applications
- Interview questions
- General content
- Cost: ~$0.01/1K tokens

**Pro (Most Capable)**
- Complex reasoning
- Overall study plan design
- Strategic decisions
- Cost: ~$0.10/1K tokens

### 2. Cascaded Generation Strategy

**Why Cascade?**
- Quality: Different models for different complexity
- Cost: Use expensive models only when needed
- Efficiency: Parallel generation of detailed content

**How it Works:**
```
1. Macro Tier (Gemini Pro):
   Input: Skill gaps, target occupation
   Output: Overall study plan structure (5-10 modules)
   
2. Meso Tier (Gemini Flash-Lite):
   Input: Each module outline
   Output: Detailed lessons (10-20 per module)
   Process: Parallel generation
   
3. Micro Tier (Vector DB / External APIs):
   Input: Lesson topics
   Output: Specific learning resources
   Process: Database lookup + web scraping
```

### 3. Batch API for Cost Savings

**Normal API**: Immediate response, full cost
```python
response = model.generate_content(prompt)  # Costs $X
```

**Batch API**: Delayed response (up to 24h), 50% discount
```python
batch_job = batch_api.submit(prompts)  # Costs $X/2
# Process results when ready (12-24 hours later)
```

**When to Use Batch:**
- Study plan generation (not urgent)
- Bulk content creation
- Non-real-time tasks

### 4. Context Caching (90% Savings!)

**Problem**: Repeated prompts waste tokens
```python
# Without caching - pays for full prompt every time
for lesson in modules:
    prompt = LONG_SYSTEM_PROMPT + lesson_specific_part
    generate(prompt)  # Costs tokens for full prompt each time
```

**Solution**: Cache static context
```python
# Cache the system prompt (50K tokens)
cached = model.cache_context(LONG_SYSTEM_PROMPT)

# Only pay for variable part
for lesson in modules:
    generate(cached + lesson_specific_part)  # 90% cheaper!
```

## 📖 Resources

- [Gemini API Docs](https://ai.google.dev/docs)
- [Django Channels](https://channels.readthedocs.io/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

## 🚀 Success Criteria

- [x] Gemini API integrated with all 3 models
- [x] Study plans generated for skill gaps
- [x] Lessons created with detailed content
- [x] CFU quizzes auto-generated
- [x] Remediation works for failed quizzes
- [x] Batch API processes jobs
- [x] Context caching reduces costs
- [x] WebSocket sends progress updates

## 🎯 Next Steps (Day 4 Preview)

Tomorrow: Mock interview simulator with real-time AI, speech-to-text, and three-judge evaluation system!
