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