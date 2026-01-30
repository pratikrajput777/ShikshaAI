from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ConversationSession, InterviewTurn
import logging

logger = logging.getLogger(__name__)

class InterviewConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time mock interviews."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'interview_{self.session_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Interview WebSocket connected: session {self.session_id}")
        
        # Send welcome and first question
        await self.send_welcome_message()
        await self.send_first_question()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Interview WebSocket disconnected: session {self.session_id}")
    
    async def receive_json(self, content):
        """
        Handle incoming WebSocket messages.
        
        Message types:
        - user_answer: Candidate's answer (from speech-to-text)
        - request_next: Request next question
        - end_interview: End session early
        """
        message_type = content.get('type')
        
        if message_type == 'user_answer':
            await self.handle_user_answer(content)
        elif message_type == 'request_next':
            await self.send_next_question()
        elif message_type == 'end_interview':
            await self.end_interview()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def send_welcome_message(self):
        """Send welcome message to candidate."""
        await self.send_json({
            'type': 'welcome',
            'message': 'Welcome to your mock interview. Take a deep breath and relax!'
        })
    
    async def send_first_question(self):
        """Generate and send opening question."""
        from interview.services import InterviewService
        service = InterviewService()
        
        session = await self.get_session()
        question = await database_sync_to_async(service.generate_first_question)(session)
        
        # Generate TTS audio
        audio_url = await database_sync_to_async(service.generate_tts_audio)(question)
        
        # Save turn
        await self.save_turn('interviewer', question, audio_url)
        
        # Send to client
        await self.send_json({
            'type': 'question',
            'question': question,
            'audio_url': audio_url,
            'question_number': 1
        })
    
    async def send_next_question(self):
        """Generate and send follow-up question."""
        from interview.services import InterviewService
        service = InterviewService()
        
        session = await self.get_session()
        
        # Check if interview complete
        if session.current_question_number >= session.target_question_count:
            await self.end_interview()
            return
        
        # Get conversation history
        history = await self.get_conversation_history()
        
        # Generate question
        question = await database_sync_to_async(service.generate_follow_up_question)(
            session, history
        )
        
        # Generate audio
        audio_url = await database_sync_to_async(service.generate_tts_audio)(question)
        
        # Save turn
        await self.save_turn('interviewer', question, audio_url)
        
        # Send
        await self.send_json({
            'type': 'question',
            'question': question,
            'audio_url': audio_url,
            'question_number': session.current_question_number + 1
        })
    
    async def handle_user_answer(self, content):
        """
        Process candidate's answer.
        
        Args:
            content: dict with 'transcript' key
        """
        transcript = content.get('transcript', '')
        
        # Save answer turn
        await self.save_turn('candidate', transcript)
        
        # Send acknowledgment
        await self.send_json({
            'type': 'answer_received',
            'message': 'Got it! Thinking...'
        })
        
        # Send next question
        await self.send_next_question()
    
    async def end_interview(self):
        """End interview and trigger evaluation."""
        from interview.tasks import evaluate_interview_task
        
        session = await self.get_session()
        await database_sync_to_async(self._update_session_status)(session, 'completed')
        
        # Queue evaluation
        await database_sync_to_async(evaluate_interview_task.delay)(self.session_id)
        
        await self.send_json({
            'type': 'interview_ended',
            'message': 'Interview complete! Generating your evaluation...'
        })
    
    # Database helpers
    @database_sync_to_async
    def get_session(self):
        return ConversationSession.objects.get(id=self.session_id)
    
    @database_sync_to_async
    def save_turn(self, speaker, text, audio_url=''):
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
    
    @database_sync_to_async
    def get_conversation_history(self):
        session = ConversationSession.objects.get(id=self.session_id)
        return list(session.turns.order_by('turn_number'))
    
    @staticmethod
    def _update_session_status(session, status):
        session.status = status
        session.save()