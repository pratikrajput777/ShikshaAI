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