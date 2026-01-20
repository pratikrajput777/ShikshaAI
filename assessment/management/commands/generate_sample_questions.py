
from django.core.management.base import BaseCommand
from assessment.models import QuestionBank
from skills.models import Skill
import random
  
class Command(BaseCommand):
      help = 'Generate sample IRT-calibrated questions'
      
      def handle(self, *args, **options):
          skills = Skill.objects.all()[:5]
          
          for skill in skills:
              # Generate 20 questions per skill across difficulty range
              for i in range(20):
                  difficulty_b = random.uniform(-2.0, 2.0)
                  discrimination_a = random.uniform(0.8, 2.0)
                  
                  QuestionBank.objects.create(
                      skill=skill,
                      question_text=f"Sample {skill.preferred_label} question {i+1} (b={difficulty_b:.2f})",
                      options=[
                          f"Option A for difficulty {difficulty_b:.1f}",
                          f"Option B for difficulty {difficulty_b:.1f}",
                          f"Option C for difficulty {difficulty_b:.1f}",
                          f"Option D for difficulty {difficulty_b:.1f}",
                      ],
                      correct_answer=random.randint(0, 3),
                      difficulty_b=difficulty_b,
                      discrimination_a=discrimination_a,
                      guessing_c=0.25,
                      generated_by_ai=False
                  )
              
              self.stdout.write(
                  self.style.SUCCESS(
                      f'Generated 20 questions for {skill.preferred_label}'
                  )
              )
  