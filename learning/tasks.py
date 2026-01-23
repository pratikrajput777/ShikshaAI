from celery import shared_task
from .models import StudyPlan
from .services import StudyPlanService

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
  
@shared_task(bind=True, max_retries=3)
def generate_study_plan_batch_task(self, study_plan_id):
      """Background task for study plan generation."""
      try:
          study_plan = StudyPlan.objects.get(id=study_plan_id)
          service = StudyPlanService()
          
          # Macro generation (Gemini Pro)
          service.generate_macro_plan(study_plan.user, study_plan.target_occupation)
          
          # Meso generation (Gemini Flash-Lite) - parallel
          service.generate_all_lessons(study_plan)
          
          return f"Study plan {study_plan_id} generated successfully"
          
      except Exception as exc:
          self.retry(exc=exc, countdown=60)

  
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