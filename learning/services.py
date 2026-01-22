import json
from django.db import transaction

from core.gemini_service import GeminiService
from .models import (
    StudyPlan,
    LearningModule,
    Lesson,
    CFUQuiz,
    Remediation
)
from assessment.services import AssessmentService
from skills.models import Skill


class StudyPlanService:
    """
    Service for AI-powered learning workflows.
    Covers:
    - Study Plan generation
    - Lesson generation
    - CFU Quiz generation
    - Remediation generation
    """

    def __init__(self):
        self.gemini = GeminiService()

    # ==========================================================
    # MACRO TIER – STUDY PLAN
    # ==========================================================

    @staticmethod
    def create_macro_plan_prompt(user, target_occupation, skill_gaps):
        gaps_summary = "\n".join([
            f"- {g.skill.preferred_label}: "
            f"Gap {g.gap_score:.2f} (Priority {g.priority_score:.2f})"
            for g in skill_gaps[:10]
        ])

        return f"""
You are an expert learning path designer.

Target Role: {target_occupation.preferred_label}
User Background: {user.experience_years} years experience, {user.skill_level}

Skill Gaps:
{gaps_summary}

Return ONLY valid JSON.

{{
  "modules": [
    {{
      "title": "Module title",
      "description": "What student will learn",
      "primary_skill": "Skill name",
      "estimated_hours": 20,
      "order": 1
    }}
  ]
}}
""".strip()

    def generate_macro_plan(self, user, target_occupation):
        with transaction.atomic():
            skill_gaps = AssessmentService.calculate_skill_gaps(
                user, target_occupation
            )

            study_plan = StudyPlan.objects.create(
                user=user,
                target_occupation=target_occupation,
                status="generating",
                skill_gaps_snapshot={
                    "gaps": [
                        {
                            "skill": g.skill.preferred_label,
                            "gap_score": g.gap_score,
                            "priority": g.priority_score
                        }
                        for g in skill_gaps[:10]
                    ]
                }
            )

            prompt = self.create_macro_plan_prompt(
                user, target_occupation, skill_gaps
            )
            study_plan.generation_prompt = prompt
            study_plan.save()

            response = self.gemini.generate_with_retry(
                prompt, model_type="pro"
            )
            data = self.gemini.parse_json_response(response)

            modules = data.get("modules", [])

            for m in modules:
                skill = Skill.objects.filter(
                    preferred_label__icontains=m.get("primary_skill", "")
                ).first()

                LearningModule.objects.create(
                    study_plan=study_plan,
                    title=m["title"],
                    description=m["description"],
                    primary_skill=skill,
                    estimated_hours=m["estimated_hours"],
                    order=m["order"]
                )

            study_plan.status = "ready"
            study_plan.total_modules = len(modules)
            study_plan.save()

            return study_plan

    # ==========================================================
    # MESO TIER – LESSONS
    # ==========================================================

    @staticmethod
    def create_lesson_prompt(module):
        return f"""
Generate lessons for a module.

Module: {module.title}
Description: {module.description}

Return ONLY valid JSON.

{{
  "lessons": [
    {{
      "title": "Lesson title",
      "content": "500–800 words",
      "learning_objectives": ["Obj1", "Obj2"],
      "estimated_minutes": 45,
      "order": 1
    }}
  ]
}}
""".strip()

    def generate_lessons_for_module(self, module):
        prompt = self.create_lesson_prompt(module)

        response = self.gemini.generate_with_retry(
            prompt, model_type="lite"
        )
        data = self.gemini.parse_json_response(response)

        created = []

        for l in sorted(
            data.get("lessons", []),
            key=lambda x: x.get("order", 0)
        ):
            lesson = Lesson.objects.create(
                module=module,
                title=l["title"],
                content=l["content"],
                learning_objectives=l.get("learning_objectives", []),
                estimated_minutes=l["estimated_minutes"],
                order=l["order"],
                status="available" if l["order"] == 1 else "locked",
                generation_prompt=prompt
            )
            created.append(lesson)

        return created

    # ==========================================================
    # CFU QUIZ GENERATION
    # ==========================================================

    @staticmethod
    def create_cfu_quiz_prompt(lesson):
        objectives = lesson.learning_objectives or []

        return f"""
Create a Check for Understanding (CFU) quiz.

Lesson: {lesson.title}

Learning Objectives:
{chr(10).join(f"- {o}" for o in objectives)}

Rules:
- Exactly 5 multiple-choice questions
- Difficulty: 2 easy, 2 medium, 1 hard
- Conceptual understanding
- JSON ONLY (no text, no markdown)

{{
  "questions": [
    {{
      "question": "Question text?",
      "options": ["A", "B", "C", "D"],
      "correct_answer": 0,
      "explanation": "Why this is correct",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}
""".strip()

    def generate_cfu_quiz(self, lesson):
        prompt = self.create_cfu_quiz_prompt(lesson)

        response = self.gemini.generate_with_retry(
            prompt, model_type="lite"
        )
        data = self.gemini.parse_json_response(response)

        questions = data.get("questions", [])

        if len(questions) != 5:
            raise ValueError("CFU quiz must contain exactly 5 questions")

        return CFUQuiz.objects.create(
            lesson=lesson,
            questions=questions,
            passing_score=70,
            generation_prompt=prompt
        )

    # ==========================================================
    # REMEDIATION
    # ==========================================================

    def generate_remediation(self, cfu_attempt):
        lesson = cfu_attempt.quiz.lesson
        wrong = []

        for ans, q in zip(
            cfu_attempt.answers,
            cfu_attempt.quiz.questions
        ):
            if ans != q["correct_answer"]:
                wrong.append({
                    "question": q["question"],
                    "user_answer": (
                        q["options"][ans]
                        if ans < len(q["options"]) else "Invalid"
                    ),
                    "correct_answer": q["options"][q["correct_answer"]],
                    "explanation": q["explanation"]
                })

        prompt = f"""
Create remediation content.

Lesson: {lesson.title}

Wrong Answers:
{json.dumps(wrong, indent=2)}

JSON ONLY:
{{
  "misconception": "Main issue",
  "explanation": "Explanation",
  "simplified_content": "300–400 words",
  "additional_examples": ["Example 1", "Example 2"]
}}
""".strip()

        response = self.gemini.generate_with_retry(
            prompt, model_type="flash"
        )
        data = self.gemini.parse_json_response(response)

        with transaction.atomic():
            remediation = Remediation.objects.create(
                cfu_attempt=cfu_attempt,
                misconception=data["misconception"],
                explanation=data["explanation"],
                simplified_content=data["simplified_content"],
                additional_examples=data["additional_examples"]
            )

            cfu_attempt.remediation_generated = True
            cfu_attempt.save(update_fields=["remediation_generated"])

        return remediation

