# Day 04: Detailed Tasks Breakdown - Mock Interview Simulator

## Developer Assignment
- **Developer A (DA)**: Interview models, WebSocket consumer, session management
- **Developer B (DB)**: Question generation, TTS integration, three-judge evaluation

---

## Phase 1: Interview Models & Database (1.5 hours)

### Task 1.1: ConversationSession Model
**Assigned to**: DA | **Duration**: 45 minutes

```python
# interview/models.py
from django.db import models
from django.conf import settings

class ConversationSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('evaluated', 'Evaluated'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_sessions')
    occupation = models.ForeignKey('skills.Occupation', on_delete=models.CASCADE, null=True, blank=True)
    job_description = models.TextField(blank=True)
    
    # Session state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_question_number = models.IntegerField(default=0)
    target_question_count = models.IntegerField(default=10)
    
    # AI model tracking
    question_generator_model = models.CharField(max_length=50, default='gemini-1.5-flash')
    evaluator_model = models.CharField(max_length=50, default='gemini-1.5-pro')
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, bla nk=True)
    
    class Meta:
        db_table = 'conversation_sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['started_at']),
        ]

class InterviewTurn(models.Model):
    SPEAKER_CHOICES = [('interviewer', 'Interviewer (AI)'), ('candidate', 'Candidate (User)')]
    
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name='turns')
    turn_number = models.IntegerField()
    speaker = models.CharField(max_length=20, choices=SPEAKER_CHOICES)
    text_content = models.TextField()
    audio_url = models.URLField(max_length=500, blank=True)
    
    # Sentiment analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    
    # Timing
    duration_seconds = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interview_turns'
        ordering = ['turn_number']
        unique_together = ['session', 'turn_number']

class InterviewEvaluation(models.Model):
    session = models.OneToOneField(ConversationSession, on_delete=models.CASCADE, related_name='evaluation')
    
    # Three-judge scores (0.0 - 1.0)
    technical_score = models.FloatField()
    behavioral_score = models.FloatField()
    structural_score = models.FloatField()
    
    # Aggregated score
    overall_score = models.FloatField()
    
    # Detailed feedback (JSON)
    technical_feedback = models.JSONField(default=dict)
    behavioral_feedback = models.JSONField(default=dict)
    structural_feedback = models.JSONField(default=dict)
    
    # Summary
    overall_feedback = models. TextField()
    improvement_areas = models.JSONField(default=list)
    
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interview_evaluations'
```

---

## Phase 2: WebSocket Consumer (2 hours)

### Task 2.1: Interview WebSocket Consumer
**Assigned to**: DA | **Duration**: 2 hours

```python
# interview/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ConversationSession, InterviewTurn
import json

class InterviewConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'interview_{self.session_id}'
        
        # Join room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send welcome and first question
        await self.send_welcome_message()
        await self.send_first_question()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive_json(self, content):
        message_type = content.get('type')
        
        if message_type == 'user_answer':
            await self.handle_user_answer(content)
        elif message_type == 'request_next_question':
            await self.send_next_question()
        elif message_type == 'end_interview':
            await self.end_interview()
    
    async def handle_user_answer(self, content):
        transcript = content.get('transcript')
        
        # Save answer turn
        await self.save_interview_turn('candidate', transcript)
        
        # Check if interview complete
        session = await self.get_session()
        if session.current_question_number >= session.target_question_count:
            await self.end_interview()
        else:
            await self.send_next_question()
    
    async def send_first_question(self):
        from .services import InterviewService
        service = InterviewService()
        
        session = await self.get_session()
        question = await database_sync_to_async(service.generate_first_question)(session)
        
        # Generate TTS audio
        audio_url = await database_sync_to_async(service.generate_tts_audio)(question)
        
        # Save question turn
        await self.save_interview_turn('interviewer', question, audio_url)
        
        # Send to client
        await self.send_json({
            'type': 'question',
            'question': question,
            'audio_url': audio_url,
            'question_number': session.current_question_number
        })
    
    async def send_next_question(self):
        from .services import InterviewService
        service = InterviewService()
        
        session = await self.get_session()
        conversation_history = await self.get_conversation_history()
        
        question = await database_sync_to_async(service.generate_follow_up_question)(
            session, conversation_history
        )
        
        audio_url = await database_sync_to_async(service.generate_tts_audio)(question)
        await self.save_interview_turn('interviewer', question, audio_url)
        
        await self.send_json({
            'type': 'question',
            'question': question,
            'audio_url': audio_url,
            'question_number': session.current_question_number
        })
    
    async def end_interview(self):
        # Trigger evaluation
        from .tasks import evaluate_interview_task
        
        session = await self.get_session()
        await database_sync_to_async(session.update)(status='completed')
        
        # Queue evaluation task
        task = await database_sync_to_async(evaluate_interview_task.delay)(self.session_id)
        
        await self.send_json({
            'type': 'interview_ended',
            'message': 'Interview complete! Generating evaluation...'
        })
    
    @database_sync_to_async
    def get_session(self):
        return ConversationSession.objects.get(id=self.session_id)
    
    @database_sync_to_async
    def save_interview_turn(self, speaker, text, audio_url=''):
        session = ConversationSession.objects.get(id=self.session_id)
        turn_number = session.turns.count() + 1
        
        InterviewTurn.objects.create(
            session=session,
            turn_number=turn_number,
            speaker=speaker,
            text_content=text,
            audio_url=audio_url
        )
        
        if speaker == 'interviewer':
            session.current_question_number += 1
            session.save()
```

**Routing** (`interview/routing.py`):
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/interview/(?P<session_id>\d+)/$', consumers.InterviewConsumer.as_asgi()),
]
```

---

## Phase 3: Question Generation & TTS (2 hours)

### Task 3.1: Interview Service - Question Generation
**Assigned to**: DB | **Duration**: 1.5 hours

```python
# interview/services.py
from core.gemini_service import GeminiService
from .models import ConversationSession, InterviewTurn

class InterviewService:
    def __init__(self):
        self.gemini = GeminiService()
    
    def generate_first_question(self, session):
        """Generate opening question based on job description."""
        prompt = f"""You are conducting a job interview.

**Role**: {session.occupation.preferred_label if session.occupation else 'General'}
**Job Description**: {session.job_description or 'Standard interview'}
**Candidate Background**: {session.user.experience_years} years experience

Generate an opening ice-breaker question that:
1. Makes candidate comfortable
2. Relates to their background
3. Is open-ended
4. Takes 2-3 minutes to answer

Respond with ONLY the question text, no preamble.
"""
        
        question = self.gemini.generate_with_retry(prompt, model_type='flash')
        return question.strip()
    
    def generate_follow_up_question(self, session, conversation_history):
        """Generate contextual follow-up question."""
        # Format history
        history_text = "\n".join([
            f"{'Interviewer' if turn.speaker == 'interviewer' else 'Candidate'}: {turn.text_content}"
            for turn in conversation_history[-6:]  # Last 3 exchanges
        ])
        
        prompt = f"""You are conducting a job interview.

**Role**: {session.occupation.preferred_label if session.occupation else 'General'}
**Question #{session.current_question_number + 1}** of {session.target_question_count}

**Conversation so far**:
{history_text}

Generate the next interview question that:
1. Builds on previous answers
2. Probes deeper into mentioned experiences
3. Covers different aspects (technical, behavioral, situational)
4. Is specific and focused
5. Allows 2-3 minute answer

Question types to mix:
- Technical: "Explain how you would..."
- Behavioral: "Tell me about a time when..."
- Situational: "What would you do if..."
- Problem-solving: "How would you approach..."

Respond with ONLY the question, no preamble.
"""
        
        question = self.gemini.generate_with_retry(prompt, model_type='flash')
        return question.strip()
```

### Task 3.2: Google Cloud TTS Integration
**Assigned to**: DB | **Duration**: 30 minutes

```python
# interview/services.py (continued)
from google.cloud import texttospeech
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

class InterviewService:
    # ... previous methods ...
    
    def generate_tts_audio(self, text):
        """Generate audio for interviewer question using Google Cloud TTS."""
        try:
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Professional male voice
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-D",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.95,  # Slightly slower for clarity
                pitch=0.0
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Save audio file
            filename = f'interview_tts/{uuid.uuid4()}.mp3'
            path = default_storage.save(filename, ContentFile(response.audio_content))
            
            return default_storage.url(path)
            
        except Exception as e:
            # Fallback: return empty (client will show text only)
            print(f"TTS generation failed: {e}")
            return ''
```

---

## Phase 4: Three-Judge Evaluation (2.5 hours)

### Task 4.1: Technical Judge
**Assigned to**: DB | **Duration**: 50 minutes

```python
# interview/judges.py
class TechnicalJudge:
    """Evaluates technical knowledge and problem-solving."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    def evaluate(self, session, turns):
        """Evaluate technical competency."""
        # Extract Q&A pairs
        qa_pairs = self._extract_qa_pairs(turns)
        
        prompt = f"""You are a TECHNICAL JUDGE evaluating an interview.

**Role**: {session.occupation.preferred_label}
**Questions & Answers**:
{qa_pairs}

Evaluate the candidate's TECHNICAL performance:

**Criteria**:
1. Technical Accuracy (30%): Correctness of facts and concepts
2. Depth of Knowledge (30%): Detail level and expertise shown
3. Problem-Solving (20%): Approach to technical challenges
4. Technical Communication (20%): Ability to explain complex topics

**Output Format** (JSON):
{{
  "score": 0.0-1.0,
  "strengths": ["strength1", "strength2", ...],
  "weaknesses": ["weakness1", "weakness2", ...],
  "suggestions": ["suggestion1", "suggestion2", ...],
  "detailed_feedback": "Paragraph explanation"
}}

Be fair but rigorous. Score: 0.7+ is good, 0.85+ is excellent.
Provide only valid JSON.
"""
        
        response = self.gemini.generate_with_retry(prompt, model_type='pro')
        return self.gemini.parse_json_response(response)
```

### Task 4.2: Behavioral Judge
**Assigned to**: DB | **Duration**: 50 minutes

```python
class BehavioralJudge:
    """Evaluates soft skills and STAR method."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    def evaluate(self, session, turns):
        qa_pairs = self._extract_qa_pairs(turns)
        
        prompt = f"""You are a BEHAVIORAL JUDGE evaluating an interview.

**Role**: {session.occupation.preferred_label}
**Questions & Answers**:
{qa_pairs}

Evaluate BEHAVIORAL/SOFT SKILLS:

**STAR Method Compliance**:
- Situation: Clear context?
- Task: Specific responsibility?
- Action: What they did?  
- Result: Outcomes and learning?

**Criteria**:
1. STAR Structure (30%): Complete stories with S-T-A-R
2. Leadership & Teamwork (25%): Collaboration examples
3. Communication (25%): Clarity and professionalism
4. Self-Awareness (20%): Growth mindset, learning from failures

**Output Format** (JSON):
{{
  "score": 0.0-1.0,
  "star_compliance": 0.0-1.0,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["..."],
  "detailed_feedback": "..."
}}

Provide only valid JSON.
"""
        
        response = self.gemini.generate_with_retry(prompt, model_type='pro')
        return self.gemini.parse_json_response(response)
```

### Task 4.3: Structural Judge
**Assigned to**: DB | **Duration**: 50 minutes

```python
class StructuralJudge:
    """Evaluates answer organization and clarity."""
    
    def __init__(self, gemini_service):
        self.gemini = gemini_service
    
    def evaluate(self, session, turns):
        qa_pairs = self._extract_qa_pairs(turns)
        
        prompt = f"""You are a STRUCTURAL JUDGE evaluating interview answers.

**Questions & Answers**:
{qa_pairs}

Evaluate ANSWER STRUCTURE and DELIVERY:

**Criteria**:
1. Organization (30%): Logical flow, clear structure
2. Conciseness (25%): No rambling, right level of detail
3. Completeness (25%): Answers the question fully
4. Professionalism (20%): Language, tone, confidence

**Output Format** (JSON):
{{
  "score": 0.0-1.0,
  "avg_answer_clarity": 0.0-1.0,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": ["Use frameworks like 'First, Second, Finally'", ...],
  "detailed_feedback": "..."
}}

Provide only valid JSON.
"""
        
        response = self.gemini.generate_with_retry(prompt, model_type='pro')
        return self.gemini.parse_json_response(response)
```

### Task 4.4: Aggregate Evaluation
**Assigned to**: DB | **Duration**: remains part of final phase for integration

```python
# interview/tasks.py
from celery import shared_task
from .models import ConversationSession, InterviewEvaluation
from .judges import TechnicalJudge, BehavioralJudge, StructuralJudge
from core.gemini_service import GeminiService

@shared_task
def evaluate_interview_task(session_id):
    """Celery task for three-judge evaluation."""
    session = ConversationSession.objects.get(id=session_id)
    turns = session.turns.all()
    
    gemini = GeminiService()
    
    # Three judges evaluate independently
    tech_judge = TechnicalJudge(gemini)
    tech_eval = tech_judge.evaluate(session, turns)
    
    behav_judge = BehavioralJudge(gemini)
    behav_eval = behav_judge.evaluate(session, turns)
    
    struct_judge = StructuralJudge(gemini)
    struct_eval = struct_judge.evaluate(session, turns)
    
    # Weighted aggregate score
    overall_score = (
        tech_eval['score'] * 0.40 +
        behav_eval['score'] * 0.35 +
        struct_eval['score'] * 0.25
    )
    
    # Combine improvement areas
    improvement_areas = (
        tech_eval.get('weaknesses', []) +
        behav_eval.get('weaknesses', []) +
        struct_eval.get('weaknesses', [])
    )
    
    # Create evaluation record
    InterviewEvaluation.objects.create(
        session=session,
        technical_score=tech_eval['score'],
        behavioral_score=behav_eval['score'],
        structural_score=struct_eval['score'],
        overall_score=overall_score,
        technical_feedback=tech_eval,
        behavioral_feedback=behav_eval,
        structural_feedback=struct_eval,
        overall_feedback=f"Overall interview performance: {overall_score * 100:.1f}%",
        improvement_areas=improvement_areas[:5]  # Top 5
    )
    
    session.status = 'evaluated'
    session.save()
    
    return f"Interview {session_id} evaluated: {overall_score:.2f}"
```

---

## Summary Checklist

### Must Complete Today
- [x] Interview models created
- [x] WebSocket consumer handling conversations
- [x] Web Speech API integrated (client-side)
- [x] Google Cloud TTS generating audio
- [x] Context-aware question generation
- [x] Three-judge evaluation system
- [x] Real-time bidirectional communication
- [x] Interview history stored

### Time Tracking

| Phase | Estimated | Actual |
|-------|-----------|--------|
| Models & DB | 1.5h | |
| WebSocket | 2h | |
| Question & TTS | 2h | |
| Three Judges | 2.5h | |
| **Total** | **8h** | |

---

**Ready for real-time AI interviews!** 🎤
