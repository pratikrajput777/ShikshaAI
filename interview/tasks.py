from celery import shared_task
from .models import ConversationSession, InterviewEvaluation
from .judges import TechnicalJudge, BehavioralJudge, StructuralJudge
from core.gemini_service import GeminiService

@shared_task
def evaluate_interview_task(session_id):
    """Celery task for three-judge evaluation."""
    session = ConversationSession.objects.get(id=session_id)
    turns = session.turns.all()
    
    gemini = GeminiService()
    
    # Three judges evaluate independently
    tech_judge = TechnicalJudge(gemini)
    tech_eval = tech_judge.evaluate(session, turns)
    
    behav_judge = BehavioralJudge(gemini)
    behav_eval = behav_judge.evaluate(session, turns)
    
    struct_judge = StructuralJudge(gemini)
    struct_eval = struct_judge.evaluate(session, turns)
    
    # Weighted aggregate score
    overall_score = (
        tech_eval['score'] * 0.40 +
        behav_eval['score'] * 0.35 +
        struct_eval['score'] * 0.25
    )
    
    # Combine improvement areas
    improvement_areas = (
        tech_eval.get('weaknesses', []) +
        behav_eval.get('weaknesses', []) +
        struct_eval.get('weaknesses', [])
    )
    
    # Create evaluation record
    InterviewEvaluation.objects.create(
        session=session,
        technical_score=tech_eval['score'],
        behavioral_score=behav_eval['score'],
        structural_score=struct_eval['score'],
        overall_score=overall_score,
        technical_feedback=tech_eval,
        behavioral_feedback=behav_eval,
        structural_feedback=struct_eval,
        overall_feedback=f"Overall interview performance: {overall_score * 100:.1f}%",
        improvement_areas=improvement_areas[:5]  # Top 5
    )
    
    session.status = 'evaluated'
    session.save()
    
    return f"Interview {session_id} evaluated: {overall_score:.2f}"