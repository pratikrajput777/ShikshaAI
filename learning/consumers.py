from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
  
class StudyPlanProgressConsumer(AsyncJsonWebsocketConsumer):
      """WebSocket consumer for real-time study plan progress."""
      
      async def connect(self):
          self.user = self.scope['user']
          self.room_group_name = f'study_plan_{self.user.id}'
          
          # Join room group
          await self.channel_layer.group_add(
              self.room_group_name,
              self.channel_name
          )
          
          await self.accept()
      
      async def disconnect(self, close_code):
          # Leave room group
          await self.channel_layer.group_discard(
              self.room_group_name,
              self.channel_name
          )
      
      async def study_plan_update(self, event):
          """Send study plan update to WebSocket."""
          await self.send_json({
              'type': 'study_plan_update',
              'status': event['status'],
              'progress': event['progress'],
              'message': event['message']
          })