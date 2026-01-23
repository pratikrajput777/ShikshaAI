from django.urls import re_path
from . import consumers
  
websocket_urlpatterns = [
      re_path(r'ws/study-plan/progress/$', consumers.StudyPlanProgressConsumer.as_asgi()),
  ]

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
  
@shared_task(bind=True)
def generate_study_plan_batch_task(self, study_plan_id):
      channel_layer = get_channel_layer()
      
      def send_update(status, progress, message):
          async_to_sync(channel_layer.group_send)(
              f'study_plan_{study_plan.user.id}',
              {
                  'type': 'study_plan_update',
                  'status': status,
                  'progress': progress,
                  'message': message
              }
          )
      
      try:
          study_plan = StudyPlan.objects.get(id=study_plan_id)
          
          send_update('generating', 10, 'Analyzing skill gaps...')
          service.generate_macro_plan(...)
          
          send_update('generating', 50, 'Creating learning modules...')
          service.generate_all_lessons(...)
          
          send_update('ready', 100, 'Study plan ready!')
          
      except Exception as exc:
          send_update('error', 0, f'Generation failed: {str(exc)}')
          raise