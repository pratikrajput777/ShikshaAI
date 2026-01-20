from .models import DiagnosticSession, QuestionBank, AnswerLog
from .irt_engine import IRTEngine
from django.conf import settings
  
class AssessmentService:
      """Service layer for diagnostic assessments."""
      
      @staticmethod
      def start_session(user, skill):
          """Start a new diagnostic session."""
          session = DiagnosticSession.objects.create(
              user=user,
              skill=skill,
              current_theta=0.0,
              current_se=1.0,
              status='active'
          )
          return session
      
      @staticmethod
      def get_next_question(session):
          """Get next adaptive question for session."""
          if session.should_terminate:
              return None
          
          # Get questions already answered in this session
          answered_question_ids = session.answers.values_list(
              'question_id', flat=True
          )
          
          # Get available questions for this skill
          available_questions = QuestionBank.objects.filter(
              skill=session.skill
          ).exclude(
              id__in=answered_question_ids
          )
          
          # Select next question
          next_question = IRTEngine.select_next_question_balanced(
              session.current_theta,
              available_questions,
              session.question_count
          )
          
          return next_question
      
@staticmethod
def submit_answer(session, question, user_answer):
      """Submit answer and update theta estimate."""
      is_correct = (user_answer == question.correct_answer)
      
      # Get all answers including this one
      all_answers = list(session.answers.select_related('question'))
      answer_pattern = [a.is_correct for a in all_answers] + [is_correct]
      all_questions = [a.question for a in all_answers] + [question]
      
      # Estimate new theta
      theta_before = session.current_theta
      se_before = session.current_se
      
      estimation = IRTEngine.estimate_theta(answer_pattern, all_questions)
      theta_after = estimation['theta']
      se_after = estimation['se']
      
      # Log the answer
      answer_log = AnswerLog.objects.create(
          session=session,
          question=question,
          user_answer=user_answer,
          is_correct=is_correct,
          theta_before=theta_before,
          theta_after=theta_after,
          se_before=se_before,
          se_after=se_after
      )
      
      # Update session
      session.current_theta = theta_after
      session.current_se = se_after
      session.question_count += 1
      
      if session.should_terminate:
          session.status = 'converged' if session.has_converged else 'completed'
          session.completed_at = timezone.now()
      
      session.save()
      
      # Update question stats
      question.times_used += 1
      if is_correct:
          question.times_correct += 1
      question.save()
      
      return answer_log

@staticmethod
def calculate_skill_gaps(user, target_occupation):
      """Calculate skill gaps for user targeting specific occupation."""
      from skills.models import OccupationSkill
      from users.models import UserProficiency
      
      # Get required skills for occupation
      required_skills = OccupationSkill.objects.filter(
          occupation=target_occupation
      ).select_related('skill')
      
      gaps = []
      
      for occ_skill in required_skills:
          # Get user's current proficiency
          try:
              proficiency = UserProficiency.objects.get(
                  user=user,
                  skill=occ_skill.skill
              )
              current_theta = proficiency.theta
          except UserProficiency.DoesNotExist:
              current_theta = -2.0  # Assume very low if not assessed
          
          # Calculate gap
          required_theta = occ_skill.required_proficiency_theta
          gap = required_theta - current_theta
          
          if gap > 0:  # Only gaps, not excesses
              # Calculate criticality coefficient
              importance = occ_skill.importance
              prerequisite_count = occ_skill.skill.prerequisites.count()
              dependent_count = occ_skill.skill.required_for.count()
              
              criticality = importance * (1 + 0.1 * prerequisite_count + 
                                         0.1 * dependent_count)
              
              priority = gap * criticality
              
              skill_gap = SkillGap.objects.update_or_create(
                  user=user,
                  occupation=target_occupation,
                  skill=occ_skill.skill,
                  defaults={
                      'current_level': current_theta,
                      'required_level': required_theta,
                      'gap_score': gap,
                      'criticality_coefficient': criticality,
                      'priority_score': priority
                  }
              )[0]
              
              gaps.append(skill_gap)
      
      return gaps
