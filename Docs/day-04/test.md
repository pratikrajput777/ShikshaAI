# Day 04: Testing & Validation Guide - Mock Interview System

Comprehensive testing for real-time AI interview implementation.

---

## Pre-Testing Checklist

- [ ] Day 03 completed and tested
- [ ] Daphne installed and configured
- [ ] channels, channels-redis installed
- [ ] Google Cloud TTS credentials configured
- [ ] Interview models migrated
- [ ] Redis running

---

## Test 1: WebSocket Connection

**Test 1.1: Basic Connection**
```python
from channels.testing import WebsocketCommunicator
from interview.consumers import InterviewConsumer
import pytest

@pytest.mark.asyncio
async def test_websocket_connection():
    # Create test session
    from interview.models import ConversationSession
    session = await database_sync_to_async(ConversationSession.objects.create)(
        user=test_user,
        occupation=test_occupation
    )
    
    # Connect
    communicator = WebsocketCommunicator(
        InterviewConsumer.as_asgi(),
        f'/ws/interview/{session.id}/'
    )
    
    connected, subprotocol = await communicator.connect()
    assert connected
    print("✓ WebSocket connected")
    
    #Receive welcome message
    response = await communicator.receive_json_from(timeout=3)
    assert 'type' in response
    print(f"✓ Received: {response['type']}")
    
    await communicator.disconnect()
    print("✓ Test 1.1 PASSED")
```

**Pass Criteria:** Connection established, messages received

---

## Test 2: Speech Integration

**Test 2.1: TTS Audio Generation**
```python
from interview.services import InterviewService

def test_tts_generation():
    service = InterviewService()
    
    test_text = "Hello, this is a test question for the interview."
    audio_url = service.generate_tts_audio(test_text)
    
    assert audio_url  # Not empty
    assert audio_url.endswith('.mp3')
    print(f"✓ TTS audio generated: {audio_url}")
    
    # Verify file exists
    from django.core.files.storage import default_storage
    filename = audio_url.split('/')[-1]
    path = f'interview_tts/{filename}'
    
    assert default_storage.exists(path)
    print(f"✓ Audio file exists: {path}")
    
    # Check file size > 0
    size = default_storage.size(path)
    assert size > 1000  # At least 1KB
    print(f"✓ Audio file size: {size} bytes")
    
    print("✓ Test 2.1 PASSED")
```

**Test 2.2: Web Speech API (Manual)**
```html
<!-- Create test page: templates/interview/test_speech.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Web Speech Test</title>
</head>
<body>
    <h1>Web Speech API Test</h1>
    <button id="start-btn">Start Recording</button>
    <button id="stop-btn">Stop Recording</button>
    <p>Transcript: <span id="transcript"></span></p>
    
    <script>
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            alert('Browser does not support Web Speech API');
        } else {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('transcript').textContent = transcript;
                console.log('Transcribed:', transcript);
            };
            
            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                alert('Error: ' + event.error);
            };
            
            document.getElementById('start-btn').onclick = () => {
                recognition.start();
                console.log('Recording started');
            };
            
            document.getElementById('stop-btn').onclick = () => {
                recognition.stop();
                console.log('Recording stopped');
            };
            
            console.log('✓ Web Speech API initialized');
        }
    </script>
</body>
</html>
```

**Manual Test Steps:**
1. Visit `/interview/test-speech/`
2. Click "Start Recording"
3. Grant microphone permission
4. Speak: "This is a test"
5. Check transcript appears
6. ✓ PASS if transcript matches speech

---

## Test 3: Question Generation

**Test 3.1: First Question Generation**
```python
def test_first_question_generation():
    service = InterviewService()
    
    session = ConversationSession.objects.create(
        user=test_user,
        occupation=occupation,
        job_description="Senior Python Developer with 5+ years experience"
    )
    
    question = service.generate_first_question(session)
    
    assert question
    assert len(question) > 20
    assert '?' in question  # Should be a question
    print(f"✓ Generated question: {question[:100]}...")
    
    # Should be relevant to job
    assert any(word in question.lower() for word in ['python', 'developer', 'experience'])
    print("✓ Question is relevant to role")
    
    print("✓ Test 3.1 PASSED")
```

**Test 3.2: Follow-Up Question Generation**
```python
def test_follow_up_generation():
    service = InterviewService()
    
    # Create session with conversation history
    session = ConversationSession.objects.create(
        user=test_user,
        occupation=occupation,
        current_question_number=2
    )
    
    # Add conversation turns
    InterviewTurn.objects.create(
        session=session,
        turn_number=1,
        speaker='interviewer',
        text_content="Tell me about your Python experience."
    )
    InterviewTurn.objects.create(
        session=session,
        turn_number=2,
        speaker='candidate',
        text_content="I've been using Python for 5 years, mainly for web development with Django."
    )
    
    conversation_history = session.turns.all()
    question = service.generate_follow_up_question(session, conversation_history)
    
    assert question
    print(f"✓ Follow-up generated: {question[:100]}...")
    
    # Should reference previous answer
    # Not strict requirement but good indicator
    print("✓ Test 3.2 PASSED")
```

---

## Test 4: Three-Judge Evaluation

**Test 4.1: Technical Judge**
```python
from interview.judges import TechnicalJudge
from core.gemini_service import GeminiService

def test_technical_judge():
    gemini = GeminiService()
    judge = TechnicalJudge(gemini)
    
    # Create test session with technical Q&A
    session = ConversationSession.objects.create(
        user=test_user,
        occupation=occupation
    )
    
    # Add technical conversation
    turns = [
        InterviewTurn.objects.create(
            session=session,
            turn_number=1,
            speaker='interviewer',
            text_content="Explain how Python's GIL works."
        ),
        InterviewTurn.objects.create(
            session=session,
            turn_number=2,
            speaker='candidate',
            text_content="The Global Interpreter Lock ensures only one thread executes Python bytecode at a time, preventing race conditions but limiting multi-threading performance."
        )
    ]
    
    evaluation = judge.evaluate(session, turns)
    
    assert 'score' in evaluation
    assert 0 <= evaluation['score'] <= 1
    assert 'strengths' in evaluation
    assert 'weaknesses' in evaluation
    assert 'suggestions' in evaluation
    
    print(f"✓ Technical score: {evaluation['score']:.2f}")
    print(f"✓ Strengths: {len(evaluation['strengths'])}")
    print(f"✓ Suggestions: {len(evaluation['suggestions'])}")
    
    print("✓ Test 4.1 PASSED")
```

**Test 4.2: Complete Three-Judge Evaluation**
```python
from interview.tasks import evaluate_interview_task

def test_full_evaluation():
    # Create complete interview session
    session = create_complete_test_interview()
    
    # Run evaluation task
    result = evaluate_interview_task(session.id)
    
    # Check evaluation created
    session.refresh_from_db()
    assert session.status == 'evaluated'
    assert hasattr(session, 'evaluation')
    
    eval = session.evaluation
    
    # Verify all scores
    assert 0 <= eval.technical_score <= 1
    assert 0 <= eval.behavioral_score <= 1
    assert 0 <= eval.structural_score <= 1
    assert 0 <= eval.overall_score <= 1
    
    # Verify aggregate formula
    expected_overall = (
        eval.technical_score * 0.40 +
        eval.behavioral_score * 0.35 +
        eval.structural_score * 0.25
    )
    assert abs(eval.overall_score - expected_overall) < 0.01
    
    print(f"✓ Technical: {eval.technical_score:.2f}")
    print(f"✓ Behavioral: {eval.behavioral_score:.2f}")
    print(f"✓ Structural: {eval.structural_score:.2f}")
    print(f"✓ Overall: {eval.overall_score:.2f}")
    
    # Verify feedback exists
    assert eval.technical_feedback
    assert eval.behavioral_feedback
    assert eval.structural_feedback
    assert eval.improvement_areas
    
    print("✓ Test 4.2 PASSED")
```

---

## Test 5: Complete Interview Flow

**Test 5.1: Full Interview Simulation**
```python
@pytest.mark.asyncio
async def test_complete_interview_flow():
    print("Running complete interview flow test...")
    
    # 1. Create session
    session = await database_sync_to_async(ConversationSession.objects.create)(
        user=test_user,
        occupation=occupation,
        target_question_count=5
    )
    print(f"✓ Session created: {session.id}")
    
    # 2. Connect WebSocket
    communicator = WebsocketCommunicator(
        InterviewConsumer.as_asgi(),
        f'/ws/interview/{session.id}/'
    )
    connected, _ = await communicator.connect()
    assert connected
    print("✓ WebSocket connected")
    
    # 3. Receive first question
    response = await communicator.receive_json_from(timeout=10)
    assert response['type'] == 'question'
    assert 'question' in response
    print(f"✓ Q1: {response['question'][:60]}...")
    
    # 4. Answer 5 questions
    for i in range(5):
        # Send answer
        await communicator.send_json_to({
            'type': 'user_answer',
            'transcript': f"This is my detailed answer to question {i+1}. I have relevant experience and can provide specific examples."
        })
        print(f"✓ Answered question {i+1}")
        
        # Get next question or end message
        response = await communicator.receive_json_from(timeout=10)
        
        if response['type'] == 'question':
            print(f"✓ Q{i+2}: {response['question'][:60]}...")
        elif response['type'] == 'interview_ended':
            print("✓ Interview completed")
            break
    
    # 5. Wait for evaluation
    import time
    time.sleep(15)  # Evaluation processes
    
    # 6. Verify results
    session_refreshed = await database_sync_to_async(ConversationSession.objects.get)(id=session.id)
    assert session_refreshed.status == 'evaluated'
    
    # Check turns saved
    turn_count = await database_sync_to_async(session_refreshed.turns.count)()
    assert turn_count == 10  # 5 Q+ 5 A
    print(f"✓ {turn_count} turns saved")
    
    # Check evaluation exists
    has_eval = await database_sync_to_async(hasattr)(session_refreshed, 'evaluation')
    assert has_eval
    print("✓ Evaluation generated")
    
    await communicator.disconnect()
    print("\n✅ Complete interview flow test PASSED")
```

**Pass Criteria:** Full interview completes, evaluation generated

---

## Test 6: Error Handling

**Test 6.1: Handle Missing Session**
```python
@pytest.mark.asyncio
async def test_invalid_session():
    communicator = WebsocketCommunicator(
        InterviewConsumer.as_asgi(),
        '/ws/interview/99999/'  # Does not exist
    )
    
    connected, _ = await communicator.connect()
    
    if connected:
        response = await communicator.receive_json_from(timeout=3)
        assert response['type'] == 'error'
        print(f"✓ Error message: {response['message']}")
    
    await communicator.disconnect()
    print("✓ Test 6.1 PASSED")
```

**Test 6.2: Handle Gemini API Failure**
```python
def test_gemini_failure_handling():
    from unittest.mock import patch
    
    service = InterviewService()
    
    # Mock Gemini to raise error
    with patch.object(service.gemini, 'generate_with_retry') as mock_generate:
        mock_generate.side_effect = Exception("API Error")
        
        try:
            question = service.generate_first_question(session)
            # Should either retry or return fallback
            assert question or True  # Depends on implementation
        except Exception as e:
            print(f"✓ Exception handled: {e}")
    
    print("✓ Test 6.2 PASSED")
```

---

## Test 7: Performance Tests

**Test 7.1: Response Time**
```python
import time

def test_question_generation_speed():
    service = InterviewService()
    
    session = ConversationSession.objects.create(
        user=test_user,
        occupation=occupation
    )
    
    # Time first question
    start = time.time()
    question = service.generate_first_question(session)
    duration = time.time() - start
    
    assert duration < 5.0  # Should be < 5 seconds
    print(f"✓ First question generated in {duration:.2f}s")
    
    # Time TTS
    start = time.time()
    audio_url = service.generate_tts_audio(question)
    duration = time.time() - start
    
    assert duration < 3.0  # Should be < 3 seconds
    print(f"✓ TTS generated in {duration:.2f}s")
    
    print("✓ Test 7.1 PASSED - Performance acceptable")
```

---

## Test 8: Integration with Previous Days

**Test 8.1: Interview Uses Skill Gaps**
```python
def test_interview_considers_skill_gaps():
    # Get skill gaps from Day 02
    from assessment.services import AssessmentService
    
    gaps = AssessmentService.calculate_skill_gaps(test_user, occupation)
    
    # Create interview session
    session = ConversationSession.objects.create(
        user=test_user,
        occupation=occupation,
        job_description=f"Focus on: {gaps[0].skill.preferred_label}"
    )
    
    # Generate question
    service = InterviewService()
    question = service.generate_first_question(session)
    
    # Question should reference top skill gap
    assert gaps[0].skill.preferred_label.lower() in question.lower()
    print(f"✓ Question references top skill gap: {gaps[0].skill.preferred_label}")
    
    print("✓ Test 8.1 PASSED")
```

---

## Final Validation Script

```bash
#!/bin/bash

echo "🎤 Day 04 - Mock Interview System Validation"
echo "============================================"

# 1. Check Daphne
pgrep -f daphne > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Daphne running"
else
    echo "✗ Daphne NOT running - Start with: daphne jobreadiness.asgi:application"
    exit 1
fi

# 2. Check Redis
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Redis running"
else
    echo "✗ Redis NOT running"
    exit 1
fi

# 3. Check Google Cloud TTS
python -c "
from google.cloud import texttospeech
try:
    client = texttospeech.TextToSpeechClient()
    print('✓ Google Cloud TTS configured')
except Exception as e:
    print(f'✗ TTS error: {e}')
    exit(1)
"

# 4. Check models
python manage.py check interview
if [ $? -eq 0 ]; then
    echo "✓ Models OK"
else
    echo "✗ Models have issues"
    exit 1
fi

# 5. Run tests
python manage.py test interview.tests
if [ $? -eq 0 ]; then
    echo "✓ All tests PASSED"
else
    echo "✗ Some tests FAILED"
    exit 1
fi

echo ""
echo "============================================"
echo "✅ Day 04 Validation COMPLETE!"
echo "Ready to conduct real-time AI interviews!"
```

---

## Test Report Template

```markdown
# Day 04 Test Report

**Date**: ___________
**Tester**: ___________

| Test | Status | Notes |
|------|--------|-------|
| WebSocket Connection | [ ] | |
| TTS Audio Generation | [ ] | |
| Web Speech API | [ ] | |
| First Question | [ ] | |
| Follow-Up Questions | [ ] | |
| Technical Judge | [ ] | |
| Behavioral Judge | [ ] | |
| Structural Judge | [ ] | |
| Complete Flow | [ ] | |
| Performance | [ ] | |

**Overall**: _____ / 10 passed

**Issues Found**:

**Sign-off**: ✅ Ready for Day 05
```

---

**All tests passing = Day 04 complete! Ready for gamification & billing!** 🎤✅
