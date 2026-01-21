from django.db import transaction
from core.gemini_service import GeminiService
from .models import StudyPlan, LearningModule, Lesson
from assessment.services import AssessmentService
from skills.models import Skill


class StudyPlanService:
    """
    Service for generating AI-powered study plans.
    Covers:
    - Macro Tier (Overall Study Plan)
    - Meso Tier (Detailed Lessons)
    """

    def __init__(self):
        self.gemini = GeminiService()

    # ==========================================================
    # MACRO TIER – STUDY PLAN
    # ==========================================================

    @staticmethod
    def create_macro_plan_prompt(user, target_occupation, skill_gaps):
        """Create prompt for overall study plan (Macro tier)."""

        gaps_summary = "\n".join([
            f"- {gap.skill.preferred_label}: "
            f"Gap {gap.gap_score:.2f} (Priority: {gap.priority_score:.2f})"
            for gap in skill_gaps[:10]
        ])

        prompt = f"""
You are an expert learning path designer. Create a comprehensive study plan.

Target Role: {target_occupation.preferred_label}
User Background: {user.experience_years} years experience, {user.skill_level} level

Skill Gaps (ordered by priority):
{gaps_summary}

Task:
Design a structured learning plan with 5–8 learning modules.

Output Format (JSON only):
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

Requirements:
1. Address highest priority gaps first
2. Build prerequisite skills before advanced topics
3. Time estimate per module: 10–40 hours
4. Clear progression from fundamentals to advanced
5. Practical, job-focused content

Return ONLY valid JSON.
"""
        return prompt.strip()

    def generate_macro_plan(self, user, target_occupation):
        """Generate overall study plan structure using Gemini Pro."""

        with transaction.atomic():
            # 1. Calculate skill gaps
            skill_gaps = AssessmentService.calculate_skill_gaps(
                user, target_occupation
            )

            # 2. Create StudyPlan
            study_plan = StudyPlan.objects.create(
                user=user,
                target_occupation=target_occupation,
                status="generating",
                skill_gaps_snapshot={
                    "gaps": [
                        {
                            "skill": gap.skill.preferred_label,
                            "gap_score": gap.gap_score,
                            "priority": gap.priority_score
                        }
                        for gap in skill_gaps[:10]
                    ]
                }
            )

            # 3. Generate plan using Gemini Pro
            prompt = self.create_macro_plan_prompt(
                user, target_occupation, skill_gaps
            )
            study_plan.generation_prompt = prompt
            study_plan.save()

            response = self.gemini.generate_with_retry(
                prompt, model_type="pro"
            )
            plan_data = self.gemini.parse_json_response(response)

            # 4. Create learning modules
            modules = plan_data.get("modules", [])
            for module_data in modules:
                skill = Skill.objects.filter(
                    preferred_label__icontains=module_data["primary_skill"]
                ).first()

                LearningModule.objects.create(
                    study_plan=study_plan,
                    title=module_data["title"],
                    description=module_data["description"],
                    primary_skill=skill,
                    estimated_hours=module_data["estimated_hours"],
                    order=module_data["order"]
                )

            # 5. Finalize
            study_plan.total_modules = len(modules)
            study_plan.status = "ready"
            study_plan.save()

            return study_plan

    # ==========================================================
    # MESO TIER – LESSON GENERATION
    # ==========================================================

    @staticmethod
    def create_lesson_prompt(module):
        """Create prompt for detailed lesson generation (Meso tier)."""

        prompt = f"""
Generate a detailed lesson plan for the following learning module.

Module Title: {module.title}
Module Description: {module.description}
Target Skill: {module.primary_skill.preferred_label if module.primary_skill else "General"}

Task:
Create 8–12 progressive lessons for this module.

Output Format (JSON only):
{{
  "lessons": [
    {{
      "title": "Lesson title",
      "content": "Detailed lesson content (500–800 words)",
      "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
      "estimated_minutes": 45,
      "order": 1
    }}
  ]
}}

Requirements:
1. Progressive difficulty (easy → advanced)
2. Beginner-friendly explanations
3. Practical examples & real-world use cases
4. Code examples where applicable
5. 3–5 clear learning objectives per lesson

Return ONLY valid JSON.
"""
        return prompt.strip()

    def generate_lessons_for_module(self, module):
        """Generate detailed lessons using Gemini Flash-Lite."""

        prompt = self.create_lesson_prompt(module)

        response = self.gemini.generate_with_retry(
            prompt, model_type="lite"
        )
        lessons_data = self.gemini.parse_json_response(response)

        lessons = lessons_data.get("lessons", [])
        created_lessons = []

        # Ensure correct order
        for lesson_data in sorted(lessons, key=lambda x: x["order"]):
            status = "available" if lesson_data["order"] == 1 else "locked"

            lesson = Lesson.objects.create(
                module=module,
                title=lesson_data["title"],
                content=lesson_data["content"],
                learning_objectives=lesson_data["learning_objectives"],
                estimated_minutes=lesson_data["estimated_minutes"],
                order=lesson_data["order"],
                status=status,
                generated_by_model="gemini-2.0-flash-lite",
                generation_prompt=prompt
            )

            created_lessons.append(lesson)

        return created_lessons

    def generate_all_lessons(self, study_plan):
        """Generate lessons for all modules in a study plan."""

        for module in study_plan.learning_modules.all().order_by("order"):
            self.generate_lessons_for_module(module)

        return study_plan
