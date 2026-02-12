# Day 04: AI Agent Prompts - Mock Interview Simulator

Ready-to-use prompts for implementing real-time AI interview system.

---

## WebSocket & Real-Time Communication

### Prompt 1.1: Interview WebSocket Consumer

```
Create Django Channels WebSocket consumer in interview/consumers.py:

Class: InterviewConsumer(AsyncJsonWebsocketConsumer)

Methods:
1. connect():
   - Extract session_id from URL
   - Create room group name
   - Join channel layer group
   - Send welcome message
   - Generate and send first question

2. disconnect():
   - Leave channel layer group
   - Update session status if needed

3. receive_json(content):
   - Handle message types:
     - 'user_answer': Save answer, generate next question
     - 'request_hint': Provide guidance
     - 'end_interview': Trigger evaluation
   
4. handle_user_answer(content):
   - Extract transcript
   - Save InterviewTurn
   - Check if interview complete
   - Generate next question or end interview

5. send_question(question_text):
   - Generate TTS audio
   - Save turn to database
   - Send JSON with question and audio URL

Use async/await, database_sync_to_async for ORM operations.
Include error handling and logging.
```

---

### Prompt 1.2: WebSocket Routing

```
Create WebSocket URL routing in interview/routing.py:

1. Import re_path and consumers
2. Define websocket_urlpatterns list
3. Add route: r'ws/interview/(?P<session_id>\d+)/$'
4. Use InterviewConsumer.as_asgi()

Update main routing.py (jobreadiness/routing.py) to include:
- ProtocolTypeRouter with 'http' and 'websocket'
- AuthMiddlewareStack for WebSocket
- URLRouter with interview.routing.websocket_urlpatterns

Configure ASGI application in asgi.py.
```

---

## Speech Integration

### Prompt 2.1: Google Cloud TTS Service

```
Create TTS service in interview/tts_service.py:

Class: TTSService

Method: generate_audio(text, voice_name='en-US-Neural2-D'):
1. Initialize Google Cloud TTS client
2. Create SynthesisInput from text
3. Configure VoiceSelectionParams:
   - language_code: en-US
   - name: configurable (male/female voices available)
   - ssml_gender: MALE or FEMALE

4. Configure AudioConfig:
   - encoding: MP3
   - speaking_rate: 0.95 (slightly slower for clarity)
   - pitch: 0.0
   - effects_profile_id: ['telephony-class-application']

5. Call synthesize_speech()
6. Save audio to media storage
7. Return public URL

Handle errors gracefully, return empty string on failure.
Include voice options: professional male, professional female, casual.
```

---

### Prompt 2.2: Web Speech API Integration (Client-Side)

```
Create JavaScript for Web Speech API in templates/interview/interview_room.html:

1. Check browser support:
   - webkitSpeechRecognition or SpeechRecognition
   - Show fallback UI if not supported

2. Initialize recognition:
   - continuous: false (one answer at a time)
   - interimResults: true (show live transcript)
   - language: 'en-US'
   - maxAlternatives: 1

3. Event handlers:
   - onstart: Show recording indicator
   - onresult: Extract transcript, display, send to WebSocket
   - onerror: Handle errors (no-speech, aborted, network)
   - onend: Stop recording indicator

4. Control functions:
   - startRecording()
   - stopRecording()
   - resetRecognition()

5. WebSocket integration:
   - Send transcript when finalized
   - Handle response from server

Include microphone permission request, error messages for HTTPS requirement.
```

---

## Question Generation

### Prompt 3.1: Context-Aware Question Generator

```
Create InterviewService in interview/services.py:

Method: generate_first_question(session):

Prompt template:
"You are an experienced interviewer for {occupation}.
Candidate background: {experience_years} years, {skill_level} level.
Job requirements: {job_description}

Generate an opening question that:
- Makes candidate comfortable
- Relates to their background  
- Is open-ended
- Allows 2-3 minute answer
- Sets positive tone

Examples:
- 'Tell me about your journey in {field}...'
- 'What drew you to {occupation}?'
- 'Walk me through a recent project you're proud of...'

Provide ONLY the question text, no explanation."

Use Gemini Flash for real-time response.
```

---

### Prompt 3.2: Follow-Up Question Generator

```
Method: generate_follow_up_question(session, conversation_history):

Prompt template:
"Interview context:
Role: {occupation}
Question #{current_number} of {total}

Previous conversation:
{formatted_history}

Generate next question that:
1. Builds on previous answers (probe deeper)
2. Covers new ground (different aspect)
3. Matches question type rotation:
   - Technical skill questions
   - Behavioral (STAR method)
   - Situational scenarios
   - Problem-solving challenges

4. Adapts difficulty:
   - If candidate struggling: easier, more guided
   - If candidate excelling: harder, more complex

5. Balances coverage:
   - Ensure all key skills assessed
   - Mix depth and breadth

Question types to rotate:
- Q1-3: Technical skills
- Q4-6: Behavioral/Past experiences
- Q7-9: Situational/Future scenarios
- Q10: Candidate questions

Provide ONLY the next question."

Use conversation_history[-6:] (last 3 exchanges) for context.
```

---

## Three-Judge Evaluation

### Prompt 4.1: Technical Judge Evaluation

```
Create TechnicalJudge class in interview/judges.py:

Method: evaluate(session, turns):

Prompt template:
"You are a TECHNICAL JUDGE evaluating a {occupation} interview.

Interview Transcript:
{formatted_qa_pairs}

Evaluate TECHNICAL COMPETENCY:

**Scoring Rubric** (40% weight):
1. Technical Accuracy (30%):
   - Factual correctness
   - Understanding of concepts
   - Appropriate terminology

2. Depth of Knowledge (30%):
   - Level of detail
   - Advanced concepts mentioned
   - Multiple approaches considered

3. Problem-Solving Approach (20%):
   - Structured thinking
   - Edge cases considered
   - Trade-offs analyzed

4. Technical Communication (20%):
   - Clear explanations
   - Good analogies
   - Complex made simple

**Output JSON**:
{
  \"score\": 0.0-1.0,
  \"strengths\": [\"specific strength 1\", \"strength 2\", ...],
  \"weaknesses\": [\"specific area to improve 1\", ...],
  \"suggestions\": [\"actionable advice 1\", ...],
  \"detailed_feedback\": \"2-3 paragraph analysis\"
}

Scoring guide:
- 0.9-1.0: Exceptional, expert-level
- 0.8-0.89: Strong, above average
- 0.7-0.79: Good, meets expectations
- 0.6-0.69: Adequate, needs improvement
- Below 0.6: Significant gaps

Be specific in feedback. Provide only valid JSON."

Use Gemini Pro for complex evaluation.
```

---

### Prompt 4.2: Behavioral Judge Evaluation

```
Method: evaluate(session, turns):

Prompt template:
"You are a BEHAVIORAL JUDGE evaluating interview answers.

Interview Transcript:
{formatted_qa_pairs}

Evaluate SOFT SKILLS & BEHAVIORAL COMPETENCY:

**STAR Method Analysis** (35% weight):
For each behavioral question, check:
- S (Situation): Clear context provided?
- T (Task): Specific responsibility defined?
-A (Action): What candidate did explained?
- R (Result): Outcomes and learning stated?

**Scoring Rubric**:
1. STAR Compliance (30%):
   - Complete S-T-A-R in answers
   - Specific examples given
   - Outcomes quantified

2. Leadership & Teamwork (25%):
   - Collaboration examples
   - Taking initiative
   - Helping others grow

3. Communication Skills (25%):
   - Clarity and structure
   - Professional language
   - Active listening implied

4. Self-Awareness (20%):
   - Learning from failures
   - Growth mindset
   - Honest self-assessment

**Output JSON**:
{
  \"score\": 0.0-1.0,
  \"star_compliance\": 0.0-1.0,
  \"leadership_examples\": integer,
  \"strengths\": [...],
  \"weaknesses\": [...],
  \"suggestions\": [\"Use STAR format: 'In [situation], I [action], which resulted in [result]'\", ...],
  \"detailed_feedback\": \"...\"
}

Flag missing STAR components. Provide specific coaching."

Use Gemini Pro for nuanced evaluation.
```

---

### Prompt 4.3: Structural Judge Evaluation

```
Method: evaluate(session, turns):

Prompt template:
"You are a STRUCTURAL JUDGE evaluating answer quality.

Interview Transcript:
{formatted_qa_pairs}

Evaluate ANSWER STRUCTURE & DELIVERY:

**Scoring Rubric** (25% weight):
1. Organization & Clarity (30%):
   - Logical flow
   - Clear structure (intro-body-conclusion)
   - Transitions between points

2. Conciseness (25%):
   - No rambling
   - Right level of detail
   - Stays on topic

3. Completeness (25%):
   - Fully answers question
   - Addresses all parts
   - Provides examples

4. Professionalism (20%):
   - Appropriate language
   - Confident but humble tone
   - No filler words (um, like, you know)

**Output JSON**:
{
  \"score\": 0.0-1.0,
  \"avg_answer_length_rating\": \"too_short|appropriate|too_long\",
  \"organization_rating\": 0.0-1.0,
  \"strengths\": [...],
  \"weaknesses\": [\"Answers tend to ramble\", \"Missing clear structure\", ...],
  \"suggestions\": [\"Use framework: 'Three key points are...'\", \"Conclude with summary\", ...],
  \"detailed_feedback\": \"...\"
}

Provide specific structural coaching."
```

---

## Testing & Debugging

### Test WebSocket Connection

```
Help me test WebSocket interview system:

1. Manual test:
   - Start Daphne server
   - Open browser console
   - Connect: new WebSocket('ws://localhost:8000/ws/interview/1/')
   - Listen for messages
   - Send test message

2. Automated test using channels testing:
   ```python
   from channels.testing import WebsocketCommunicator
   from interview.consumers import InterviewConsumer
   
   async def test_interview_flow():
       communicator = WebsocketCommunicator(InterviewConsumer.as_asgi(), '/ws/interview/1/')
       connected, _ = await communicator.connect()
       assert connected
       
       # Receive first question
       response = await communicator.receive_json_from()
       assert response['type'] == 'question'
       
       # Send answer
       await communicator.send_json_to({
           'type': 'user_answer',
           'transcript': 'My answer here'
       })
       
       await communicator.disconnect()
   ```

3. Test error handling, reconnection, concurrent users.
```

---

### Debug TTS Issues

```
TTS audio not generating or playing. Debug:

1. Check Google Cloud TTS credentials:
   - GOOGLE_APPLICATION_CREDENTIALS environment variable set
   - Service account has Text-to-Speech API enabled
   - Billing enabled

2. Test TTS directly:
   ```python
   from google.cloud import texttospeech
   client = texttospeech.TextToSpeechClient()
   # Should not error
   ```

3. Check audio file storage:
   - Files saving to correct media directory
   - URLs are publicly accessible
   - CORS headers configured for audio

4. Browser audio playback:
   - Check network tab for 404s
   - Audio element src set correctly
   - Browser can play MP3 format

5. Fallback: If TTS unavailable, interview should continue text-only.
```

---

### Test Three-Judge Evaluation

```
Validate evaluation system:

1. Create test interview with known quality:
   - Excellent answers (expect scores > 0.8)
   - Poor answers (expect scores < 0.6)
   - Mixed answers (expect scores 0.6-0.8)

2. Run evaluation:
   ```python
   from interview.tasks import evaluate_interview_task
   result = evaluate_interview_task(session_id)
   ```

3. Verify:
   - All three judges return 0.0-1.0 scores
   - Feedback is specific and actionable
   - Aggregate score matches formula: tech*0.4 + behav*0.35 + struct*0.25
   - JSON parsing succeeds

4. Check consistency:
   - Same transcript → similar scores (within 0.1)
   - Temperature=0.7 for some variability but consistency

5. Validate feedback quality:
   - Specific, not generic
   - Actionable suggestions
   - References actual answers
```

---

## Performance Optimization

### Optimize Real-Time Response

```
Reduce latency in interview system:

1. Question generation:
   - Use Gemini Flash (not Pro) for speed
   - Cache common opening questions
   - Pre-generate follow-ups in background

2. TTS optimization:
   - Generate audio async (don't block)
   - Cache TTS for repeated phrases
   - Use lower quality for speed if needed

3. WebSocket:
   - Minimize message size
   - Compress large payloads
   - Use binary for audio if streaming

4. Database:
   - Async ORM queries
   - Select_related for conversation history
   - Index on session_id and turn_number

Target: < 2 seconds from answer to next question.
```

---

**Use these prompts to complete Day 04 implementation efficiently!** 🎤
