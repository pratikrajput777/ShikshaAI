from django.db.models import Q
from .models import DiagnosticSession, QuestionBank, AnswerLog, SkillGap
from skills.models import Skill
import numpy as np
from scipy.optimize import minimize_scalar
import logging

from django.db import transaction
from typing import Optional

logger = logging.getLogger(__name__)


class IRTEngine:
    """Item Response Theory calculations (3-Parameter Logistic Model)."""

    @staticmethod
    def probability(theta: float, a: float, b: float, c: float) -> float:
        """3PL probability P(theta) = c + (1-c)/(1+exp(-a*(theta-b)))"""
        return c + (1 - c) / (1 + np.exp(-a * (theta - b)))

    @staticmethod
    def information(theta: float, a: float, b: float, c: float) -> float:
        """Fisher Information at theta."""
        p = IRTEngine.probability(theta, a, b, c)
        p = np.clip(p, 0.01, 0.99)
        q = 1 - p
        p_prime = a * (p - c) * q / (1 - c)
        return (p_prime ** 2) / (p * q)

    @staticmethod
    def estimate_theta(answers: list, questions: list, initial_theta: float = 0.0) -> tuple:
        """Estimate learner ability (theta) using MLE."""
        if not answers:
            return initial_theta, 1.0

        def negative_log_likelihood(theta):
            ll = 0
            for answer, q in zip(answers, questions):
                p = IRTEngine.probability(theta, q['a'], q['b'], q['c'])
                p = np.clip(p, 0.0001, 0.9999)
                ll += np.log(p) if answer else np.log(1 - p)
            return -ll

        result = minimize_scalar(negative_log_likelihood, bounds=(-4, 4), method='bounded')
        theta = result.x
        total_info = sum(IRTEngine.information(theta, q['a'], q['b'], q['c']) for q in questions)
        se = 1.0 / np.sqrt(total_info) if total_info > 0 else 1.0
        return theta, se

    @staticmethod
    def select_next_question(theta: float, se: float, available_questions, answered_ids: set) -> Optional[QuestionBank]:
        """Select most informative next question."""
        candidates = available_questions.exclude(id__in=answered_ids)
        if not candidates.exists():
            return None

        if se > 0.5:  # early stage: spread difficulty
            target_difficulties = [theta - 1.5, theta, theta + 1.5]
            selected = None
            min_distance = float('inf')
            for q in candidates:
                for target_b in target_difficulties:
                    distance = abs(q.difficulty_b - target_b)
                    if distance < min_distance:
                        min_distance = distance
                        selected = q
            return selected

        # later stage: max information
        best_question = None
        max_info = 0
        for q in candidates[:50]:  # limit for performance
            info = IRTEngine.information(theta, q.discrimination_a, q.difficulty_b, q.guessing_c)
            if info > max_info:
                max_info = info
                best_question = q
        return best_question


class AssessmentService:
    """Main service for managing diagnostic assessments."""

    @staticmethod
    def start_session(user, skill) -> DiagnosticSession:
        session = DiagnosticSession.objects.create(
            user=user,
            skill=skill,
            current_theta=0.0,
            current_se=1.0,
            status='active'
        )
        logger.info(f"Started assessment session {session.id} for {user} on {skill}")
        return session

    @staticmethod
    def get_next_question(session: DiagnosticSession) -> Optional[QuestionBank]:
        if session.current_se < 0.3 or session.question_count >= 30:
            session.status = 'converged'
            session.save()
            logger.info(f"Session {session.id} converged at theta={session.current_theta:.2f}")
            return None

        # ✅ FIXED: use related_name 'answers'
        answered_ids = set(session.answers.values_list('question_id', flat=True))
        available = QuestionBank.objects.filter(skill=session.skill)

        next_question = IRTEngine.select_next_question(session.current_theta, session.current_se, available, answered_ids)
        return next_question

    @staticmethod
    def submit_answer(session: DiagnosticSession, question: QuestionBank, selected_answer: int) -> dict:
        is_correct = (selected_answer == question.correct_answer)

        AnswerLog.objects.create(
            session=session,
            question=question,
            user_answer=selected_answer,
            is_correct=is_correct,
            theta_before=session.current_theta,
            theta_after=session.current_theta,
            se_before=session.current_se,
            se_after=session.current_se
        )

        # ✅ FIXED: use related_name 'answers'
        logs = session.answers.select_related('question').all()
        answers = [log.is_correct for log in logs]
        questions = [{'a': log.question.discrimination_a, 'b': log.question.difficulty_b, 'c': log.question.guessing_c} for log in logs]

        new_theta, new_se = IRTEngine.estimate_theta(answers, questions, session.current_theta)
        session.current_theta = new_theta
        session.current_se = new_se
        session.question_count += 1
        session.save()

        last_log = logs.last()
        last_log.theta_after = new_theta
        last_log.se_after = new_se
        last_log.save()

        logger.info(f"Session {session.id}: theta={new_theta:.2f}, SE={new_se:.2f}")

        return {'correct': is_correct, 'theta': new_theta, 'se': new_se, 'converged': new_se < 0.3}

    @staticmethod
    def calculate_skill_gaps(user, target_occupation) -> list:
        from skills.models import OccupationSkill

        required_skills = OccupationSkill.objects.filter(occupation=target_occupation).select_related('skill')
        skill_gaps = []

        for occ_skill in required_skills:
            skill = occ_skill.skill
            required_level = occ_skill.proficiency_level
            required_theta = (required_level - 2) * 1.0

            session = DiagnosticSession.objects.filter(user=user, skill=skill, status='converged').order_by('-completed_at').first()
            current_theta = session.current_theta if session else -2.0

            gap_score = max(0, required_theta - current_theta)
            criticality = occ_skill.criticality_score / 10.0
            priority_score = gap_score * criticality

            skill_gap, _ = SkillGap.objects.update_or_create(
                user=user,
                occupation=target_occupation,
                skill=skill,
                defaults={
                    'current_level': current_theta,
                    'required_level': required_theta,
                    'gap_score': gap_score,
                    'priority_score': priority_score
                }
            )

            skill_gaps.append(skill_gap)

        skill_gaps.sort(key=lambda x: x.priority_score, reverse=True)
        logger.info(f"Calculated {len(skill_gaps)} skill gaps for {user}")
        return skill_gaps
