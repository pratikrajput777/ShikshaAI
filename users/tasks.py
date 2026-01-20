from celery import shared_task
  
@shared_task
def send_welcome_email(user_id):
      print(f"Sending welcome email to user {user_id}")
      return f"Email sent to user {user_id}"

@shared_task
def generate_skill_embeddings(skill_id):
      print(f"Generating embeddings for skill {skill_id}")
      return f"Embeddings generated for skill {skill_id}"