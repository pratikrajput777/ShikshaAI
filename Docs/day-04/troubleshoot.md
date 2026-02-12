# Day 04: Troubleshooting Guide - Mock Interview System

Solutions for WebSocket, speech, and real-time AI interview issues.

---

## WebSocket Connection Issues

### ❌ Problem: WebSocket Connection Refused

**Symptoms:**
```
WebSocket connection to 'ws://localhost:8000/ws/interview/1/' failed: Error during WebSocket handshake
```

**Solution:**
```bash
# 1. Ensure Daphne is running (not Django dev server)
daphne -b 0.0.0.0 -p 8000 jobreadiness.asgi:application

# 2. Check ASGI configuration in asgi.py
# Must have ProtocolTypeRouter, not just get_asgi_application()

# 3. Verify channels installed
pip install channels channels-redis daphne

# 4. Check settings.py
INSTALLED_APPS = [
    ...
    'channels',
]

ASGI_APPLICATION = 'jobreadiness.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    },
}

# 5. Test Redis connection
redis-cli ping  # Should return PONG
```

---

### ❌ Problem: WebSocket Connects but No Messages

**Symptoms:**
```
Connection established but no welcome message or first question
```

**Solution:**
```python
# Check consumer connect() method executes fully
async def connect(self):
    await self.accept()  # MUST call this!
    
    # Add logging
    print(f"WebSocket connected: session {self.session_id}")
    
    try:
        await self.send_welcome_message()
        await self.send_first_question()
    except Exception as e:
        print(f"Error in connect: {e}")
        await self.send_json({'type': 'error', 'message': str(e)})

# Check session exists
@database_sync_to_async
def get_session(self):
    try:
        return ConversationSession.objects.get(id=self.session_id)
    except ConversationSession.DoesNotExist:
        raise ValueError(f"Session {self.session_id} not found")
```

---

## Speech Recognition Issues

### ❌ Problem: Web Speech API Not Working

**Symptoms:**
```javascript
TypeError: webkitSpeechRecognition is not a constructor
```

**Solution:**
```javascript
// Check browser support
if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Speech recognition not supported. Please use Chrome.');
    // Show text input fallback
    document.getElementById('text-input-fallback').style.display = 'block';
    return;
}

// Use correct constructor
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

// Must be HTTPS (or localhost for development)
if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
    alert('Speech recognition requires HTTPS');
}
```

---

### ❌ Problem: Microphone Permission Denied

**Symptoms:**
```
NotAllowedError: Permission denied
```

**Solution:**
```javascript
recognition.onerror = function(event) {
    if (event.error === 'not-allowed') {
        alert('Microphone access denied. Please enable in browser settings.');
        // Show instructions for enabling mic
        showMicrophoneInstructions();
    } else if (event.error === 'no-speech') {
        console.log('No speech detected, retrying...');
        recognition.start();  // Auto-retry
    }
};

function showMicrophoneInstructions() {
    const instructions = `
    To enable microphone:
    Chrome: Click lock icon in address bar → Site settings → Microphone → Allow
    `;
    document.getElementById('mic-instructions').innerHTML = instructions;
}
```

---

## Text-to-Speech Issues

### ❌ Problem: Google Cloud TTS Authentication Failed

**Symptoms:**
```python
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:**
```bash
# 1. Set credentials environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# 2. Or in Django settings.py
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/key.json'

# 3. Verify service account has correct permissions
# Google Cloud Console → IAM → Service Account needs:
# - Cloud Text-to-Speech API User role

# 4. Enable Text-to-Speech API
# Google Cloud Console → APIs & Services → Enable Text-to-Speech API

# 5. Test credentials
from google.cloud import texttospeech
client = texttospeech.TextToSpeechClient()
print("TTS client initialized successfully")
```

---

### ❌ Problem: TTS Audio Not Playing

**Symptoms:**
```
Audio element shows but no sound plays
```

**Solution:**
```python
# 1. Check audio file is saved correctly
def generate_tts_audio(self, text):
    response = client.synthesize_speech(...)
    
    # Save with proper content type
    filename = f'interview_tts/{uuid.uuid4()}.mp3'
    path = default_storage.save(
        filename,
        ContentFile(response.audio_content)
    )
    
    # Ensure URL is publicly accessible
    url = default_storage.url(path)
    print(f"TTS audio saved: {url}")  # Debug
    
    return url

# 2. Configure CORS for audio files (if using S3/Cloud Storage)
# In storage backend, allow:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET

# 3. Check MEDIA settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 4. Serve media in development
# urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 5. Browser console - check for errors
// Network tab: 404 = file not saved/URL wrong
// Console: CORS error = headers not set
```

---

## Question Generation Issues

### ❌ Problem: Questions Too Generic/Repetitive

**Symptoms:**
```
Every interview asks same opening question
```

**Solution:**
```python
def generate_first_question(self, session):
    # Add more context for variety
    prompt = f"""You are interviewing for: {session.occupation.preferred_label}

Candidate Details:
- Experience: {session.user.experience_years} years
- Current Level: {session.user.skill_level}
- Target Role: {session.job_description[:200]}
- Background: {session.user.target_role}

Generate a UNIQUE opening question that:
1. Relates specifically to their background
2. Is conversational and warm
3. Allows them to shine
4. Is different from generic "tell me about yourself"

Examples of GOOD questions:
- "I see you have {X} years in {field}. What's been the most surprising thing you've learned?"
- "You're currently a {role}. What made you interested in moving to {target_role}?"

Provide ONLY the question, make it feel natural and specific."
"""
    
    # Use temperature for variety
    question = self.gemini.generate_with_retry(
        prompt,
        model_type='flash',
        generation_config={'temperature': 0.9}  # More creative
    )
    
    return question.strip()
```

---

### ❌ Problem: Follow-Up Questions Don't Reference Previous Answers

**Symptoms:**
```
Questions feel disconnected, don't build on conversation
```

**Solution:**
```python
def generate_follow_up_question(self, session, conversation_history):
    # Include MORE context from previous answers
    recent_exchange = conversation_history[-2:]  # Last Q&A pair
    
    last_question = recent_exchange[0].text_content if recent_exchange else ""
    last_answer = recent_exchange[1].text_content if len(recent_exchange) > 1 else ""
    
    prompt = f"""Interview Context:
Role: {session.occupation.preferred_label}
Question #{session.current_question_number + 1}

Most Recent Exchange:
Interviewer: {last_question}
Candidate: {last_answer}

Your task: Generate a follow-up question that:
1. DIRECTLY builds on something candidate mentioned in their last answer
2. Probes deeper: "You mentioned {X}, can you tell me more about..."
3. Explores implications: "That approach to {Y}, how did it affect {Z}?"
4. Asks for specifics: "Can you walk me through exactly how you..."

Make it feel like a natural conversation continuation.
Question:"""
    
    question = self.gemini.generate_with_retry(prompt, model_type='flash')
    return question.strip()
```

---

## Evaluation Issues

### ❌ Problem: Judges Give Same Score for All Interviews

**Symptoms:**
```
Every interview scores around 0.7, no differentiation
```

**Solution:**
```python
# Add more specific rubric and examples
def evaluate(self, session, turns):
    prompt = f"""You are a TECHNICAL JUDGE.

**IMPORTANT**: Be rigorous and differentiate quality!

Scoring Guide with EXAMPLES:

0.9-1.0 EXCEPTIONAL:
- Provides multiple sophisticated solutions
- Discusses trade-offs deeply
- Uses advanced concepts correctly
- Anticipates edge cases proactively

0.7-0.8 GOOD:
- Solid understanding of concepts
- One clear solution provided
- Some depth in explanation
- Basic edge cases mentioned

0.5-0.6 ADEQUATE:
- Basic understanding shown
- Solution works but naive
- Superficial explanation
- Misses important considerations

Below 0.5 WEAK:
- Incorrect concepts
- No working solution
- Cannot explain reasoning

Interview Transcript:
{qa_pairs}

Evaluate critically. Most interviews should be 0.6-0.8 range.
Only truly exceptional candidates deserve 0.9+.

Output JSON with specific, evidence-based feedback."
```

---

### ❌ Problem: Evaluation Takes Too Long (>60 seconds)

**Symptoms:**
```
User waiting several minutes for feedback
```

**Solution:**
```python
# 1. Run judges in parallel
from concurrent.futures import ThreadPoolExecutor

def evaluate_interview_parallel(session_id):
    session = ConversationSession.objects.get(id=session_id)
    turns = session.turns.all()
    gemini = GeminiService()
    
    # Run three judges concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        tech_future = executor.submit(TechnicalJudge(gemini).evaluate, session, turns)
        behav_future = executor.submit(BehavioralJudge(gemini).evaluate, session, turns)
        struct_future = executor.submit(StructuralJudge(gemini).evaluate, session, turns)
        
        tech_eval = tech_future.result()
        behav_eval = behav_future.result()
        struct_eval = struct_future.result()
    
    # Calculate aggregate
    overall_score = (
        tech_eval['score'] * 0.40 +
        behav_eval['score'] * 0.35 +
        struct_eval['score'] * 0.25
    )
    
    # Save evaluation...

# 2. Use Gemini Flash instead of Pro for faster response
# Evaluation quality vs speed trade-off

# 3. Limit transcript length passed to judges
qa_pairs = self._format_qa_pairs(turns[:20])  # Max 20 turns
```

---

## Session State Management

### ❌ Problem: Interview State Lost on Reconnect

**Symptoms:**
```
User refreshes page, conversation history gone
```

**Solution:**
```python
# 1. Resume from database on reconnect
async def connect(self):
    self.session_id = self.scope['url_route']['kwargs']['session_id']
    session = await self.get_session()
    
    # Send conversation history
    turns = await database_sync_to_async(list)(
        session.turns.all().order_by('turn_number')
    )
    
    history = [
        {
            'speaker': turn.speaker,
            'text': turn.text_content,
            'audio_url': turn.audio_url,
            'turn_number': turn.turn_number
        }
        for turn in turns
    ]
    
    await self.send_json({
        'type': 'session_restore',
        'history': history,
        'current_question': session.current_question_number,
        'status': session.status
    })
    
    # If interview was in progress, ready for next answer
    if session.status == 'active':
        await self.send_json({'type': 'ready_for_answer'})

# 2. Client-side: Store session ID in localStorage
localStorage.setItem('current_interview_session', session_id);

# 3. Timeout inactive sessions
from django.utils import timezone
from datetime import timedelta

# In Celery beat task
@periodic_task(run_every=timedelta(hours=1))
def cleanup_abandoned_interviews():
    threshold = timezone.now() - timedelta(hours=2)
    ConversationSession.objects.filter(
        status='active',
        started_at__lt=threshold
    ).update(status='abandoned')
```

---

## Performance Problems

### ❌ Problem: Slow Response Time (>5 seconds per question)

**Symptoms:**
```
Long delay between user answer and next question
```

**Solution:**
```python
# 1. Optimize database queries
def get_conversation_history(self, session):
    # Use select_related to avoid N+1 queries
    return session.turns.all().order_by('turn_number')[:10]  # Limit history

# 2. Cache TTS for common phrases
from django.core.cache import cache

def generate_tts_audio(self, text):
    cache_key = f'tts_{hashlib.md5(text.encode()).hexdigest()}'
    cached_url = cache.get(cache_key)
    
    if cached_url:
        return cached_url
    
    # Generate new
    url = self._synthesize_audio(text)
    cache.set(cache_key, url, timeout=86400)  # 24 hours
    return url

# 3. Use async for IO-bound operations
async def send_next_question(self):
    # Generate question and TTS in parallel
    import asyncio
    
    question_task = database_sync_to_async(self.service.generate_follow_up_question)(...)
    
    question = await question_task
    
    # TTS in background, send text immediately
    await self.send_json({
        'type': 'question',
        'question': question,
        'audio_url': ''  # Will send separately
    })
    
    # Generate TTS async
    audio_url = await database_sync_to_async(self.service.generate_tts_audio)(question)
    await self.send_json({
        'type': 'audio_ready',
        'audio_url': audio_url
    })
```

---

## Complete System Test

```python
# End-to-end interview test
from channels.testing import WebsocketCommunicator
from interview.consumers import InterviewConsumer

async def test_full_interview():
    # 1. Create session
    session = ConversationSession.objects.create(
        user=user,
        occupation=occupation,
        target_question_count=3  # Short test
    )
    
    # 2. Connect WebSocket
    communicator = WebsocketCommunicator(
        InterviewConsumer.as_asgi(),
        f'/ws/interview/{session.id}/'
    )
    connected, _ = await communicator.connect()
    assert connected
    
    # 3. Receive first question
    response = await communicator.receive_json_from(timeout=5)
    assert response['type'] == 'question'
    assert 'question' in response
    print(f"Q1: {response['question']}")
    
    # 4. Answer questions
    for i in range(3):
        await communicator.send_json_to({
            'type': 'user_answer',
            'transcript': f"This is my answer to question {i+1}..."
        })
        
        if i < 2:  # Not last question
            response = await communicator.receive_json_from(timeout=5)
            assert response['type'] == 'question'
            print(f"Q{i+2}: {response['question']}")
    
    # 5. Interview should end
    response = await communicator.receive_json_from(timeout=5)
    assert response['type'] == 'interview_ended'
    
    # 6. Wait for evaluation
    import time
    time.sleep(10)  # Evaluation task processes
    
    session.refresh_from_db()
    assert session.status == 'evaluated'
    assert hasattr(session, 'evaluation')
    
    eval = session.evaluation
    assert 0 <= eval.overall_score <= 1
    print(f"Scores: Tech={eval.technical_score}, Behav={eval.behavioral_score}, Struct={eval.structural_score}")
    print(f"Overall: {eval.overall_score}")
    
    await communicator.disconnect()
    print("✅ Full interview test PASSED")

# Run test
import asyncio
asyncio.run(test_full_interview())
```

---

**All issues resolved = Real-time interviews working perfectly!** 🎤✅
