# Day 04: Mock Interview Simulator & Real-Time AI Evaluation 🎤

## 📚 What You Will Achieve Today

By the end of Day 4, you will have:

1. ✅ Real-time mock interview conversation system
2. ✅ Web Speech API integration (client-side STT - FREE!)
3. ✅ Google Cloud Text-to-Speech (interviewer voice)
4. ✅ Context-aware question generation with Gemini
5. ✅ Three-judge AI evaluation system
6. ✅ WebSocket bidirectional communication
7. ✅ Interview session state management
8. ✅ Performance analytics and feedback
9. ✅ Interview history tracking

## 🎯 Learning Objectives

### Real-Time AI Applications
- **WebSocket Communication**: Bidirectional real-time messaging
- **State Management**: Maintain conversation context across turns
- **Streaming Responses**: Handle audio and text streams
- **Low-Latency Design**: Minimize response time for natural conversation

### Speech Technology
- **Web Speech API**: Browser-based speech-to-text (no cost!)
- **Google Cloud TTS**: High-quality voice synthesis
- **Audio Processing**: Handle audio streams and formats
- **Voice Selection**: Multiple languages and voices

### AI Evaluation Systems
- **Multi-Perspective Assessment**: Three independent judges
- **Rubric-Based Scoring**: Consistent evaluation criteria
- **Qualitative Feedback**: Detailed improvement suggestions
- **Aggregate Metrics**: Combined scoring methodology

## 🛠️ Technology Stack (Day 4)

| Technology | Version | Purpose |
|------------|---------|---------|
| Django Channels | 4.0.0 | WebSocket support |
| Daphne | 4.0.0 | ASGI server |
| Google Cloud TTS | 2.14.0+ | Text-to-speech |
| Web Speech API | Browser | Speech-to-text (FREE) |
| Gemini Flash | 1.5 | Real-time question generation |
| Gemini Pro | 1.5 | Three-judge evaluation |

## 📊 Database Schema (Day 4)

### New Tables
1. **conversation_sessions** - Interview session tracking
2. **interview_turns** - Question-answer pairs
3. **interview_evaluations** - Three-judge scores
4. **user_interview_scores** - Aggregate performance metrics

### Key Relationships
```
User 1→M ConversationSession 1→M InterviewTurn
ConversationSession 1→1 InterviewEvaluation
User 1→M UserInterviewScore
```

## ⏱️ Estimated Time: 8 hours

## 🎓 Key Concepts

### 1. Web Speech API (Client-Side STT)

**Why Web Speech API?**
- ✅ **FREE** - No API costs
- ✅ **Fast** - Runs in browser, low latency
- ✅ **Accurate** - Uses device's native speech recognition
- ✅ **Privacy** - Audio never leaves user's device

**How it Works:**
```javascript
// Browser-side JavaScript
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;

recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    // Send transcript to backend via WebSocket
    socket.send(JSON.stringify({
        type: 'user_answer',
        transcript: transcript
    }));
};

recognition.start();
```

**Limitations:**
- Requires HTTPS (or localhost)
- Browser support varies (Chrome best)
- Requires microphone permissions

### 2. Google Cloud Text-to-Speech

**Why Google Cloud TTS?**
- High-quality natural voices
- Multiple languages and accents
- Free tier: 1 million characters/month
- SSML support for intonation control

**Basic Usage:**
```python
from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

synthesis_input = texttospeech.SynthesisInput(text="Hello candidate")
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Neural2-D"  # Professional male voice
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

response = client.synthesize_speech(
    input=synthesis_input,
    voice=voice,
    audio_config=audio_config
)

# response.audio_content is MP3 bytes
```

### 3. Three-Judge Evaluation System

**Judges:**

**1. Technical Judge**
- Evaluates domain knowledge
- Checks factual accuracy
- Assesses technical depth
- Verifies problem-solving approach

**2. Behavioral Judge**
- STAR method compliance (Situation, Task, Action, Result)
- Communication clarity
- Leadership and teamwork examples
- Conflict resolution stories

**3. Structural Judge**
- Answer organization and clarity
- Conciseness vs completeness
- Use of examples
- Professional language

**Scoring:**
Each judge provides:
- Score: 0.0 - 1.0
- Strengths: List of positive aspects
- Weaknesses: Areas for improvement
- Suggestions: Specific advice

**Aggregate Score:**
```
Final Score = (Technical × 0.4) + (Behavioral × 0.35) + (Structural × 0.25)
```

### 4. WebSocket Communication Flow

```
1. User: Connect to WebSocket (/ws/interview/<session_id>/)
2. Server: Send welcome message
3. Server: Generate and send first question (with TTS audio)
4. User: Speak answer → Web Speech API → Send transcript
5. Server: Receive answer → Store in database
6. Server: Analyze answer → Generate follow-up
7. Server: Send next question (with TTS audio)
8. Repeat steps 4-7 for 8-12 questions
9. Server: Trigger three-judge evaluation
10. Server: Send final scores and feedback
11. User: Disconnect
```

### 5. Context-Aware Question Generation

**Strategy:**
- First question: Based on job description and user background
- Follow-ups: Based on previous answers
- Difficulty adaptation: Easier if struggling, harder if excelling
- Topic coverage: Ensure all key skills assessed

**Example Chat History:**
```python
conversation_history = [
    {"role": "interviewer", "content": "Tell me about your Python experience"},
    {"role": "candidate", "content": "I've used Python for 3 years..."},
    {"role": "interviewer", "content": "Can you describe a challenging bug you fixed?"},
    {"role": "candidate", "content": "Once I had a memory leak..."
}
]

# Next question considers this history
next_question = generate_follow_up(conversation_history, job_requirements)
```

## 📖 Resources

- [Web Speech API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Google Cloud TTS](https://cloud.google.com/text-to-speech/docs)
- [Django Channels](https://channels.readthedocs.io/)
- [STAR Interview Method](https://www.themuse.com/advice/star-interview-method)

## 🚀 Success Criteria

By end of day:

- [x] WebSocket server handles interview conversations
- [x] Client-side speech recognition captures answers
- [x] Google TTS generates interviewer voice
- [x] Questions generated based on context
- [x] Three-judge evaluation produces scores
- [x] Interview history stored and retrievable
- [x] Real-time bidirectional communication works
- [x] Session state managed correctly

## 🎯 Next Steps (Day 5 Preview)

Tomorrow: Gamification (points, achievements, leaderboards), Subscription system, Stripe payments, and Analytics dashboard!

---

**Ready to build a production-ready AI interview simulator!** 🎤
