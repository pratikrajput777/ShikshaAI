from core.gemini_service import GeminiService

class BaseJudge:
    """
    Base class for all interview judges
    """

    MODEL = "gemini-1.5-pro"
    SCORE_RANGE = (0.0, 1.0)

    def __init__(self):
        self.llm = GeminiService()

    async def judge(self, conversation):
        raise NotImplementedError("Judge must implement judge()")

class TechnicalJudge(BaseJudge):
    """
    Evaluates technical correctness, depth & problem-solving
    """

    async def judge(self, conversation):
        prompt = """
You are a technical interview judge.

Evaluate:
- Technical accuracy
- Conceptual depth
- Problem-solving ability

Return JSON:
{
  "score": float (0.0 to 1.0),
  "feedback": {
    "strengths": [],
    "weaknesses": []
  }
}
"""

        result = await self.llm.generate_json_response(
            system_prompt=prompt,
            messages=conversation,
            model=self.MODEL
        )

        return result

class BehavioralJudge(BaseJudge):
    """
    Evaluates communication, confidence & attitude
    """

    async def judge(self, conversation):
        prompt = """
You are a behavioral interview judge.

Evaluate:
- Communication clarity
- Confidence
- Professional attitude
- Examples using STAR method

Return JSON:
{
  "score": float (0.0 to 1.0),
  "feedback": {
    "positives": [],
    "concerns": []
  }
}
"""

        result = await self.llm.generate_json_response(
            system_prompt=prompt,
            messages=conversation,
            model=self.MODEL
        )

        return result

class StructuralJudge(BaseJudge):
    """
    Evaluates answer structure & logical flow
    """

    async def judge(self, conversation):
        prompt = """
You are a communication structure judge.

Evaluate:
- Answer organization
- Logical flow
- Clarity and conciseness

Return JSON:
{
  "score": float (0.0 to 1.0),
  "feedback": {
    "good_structure": [],
    "needs_improvement": []
  }
}
"""

        result = await self.llm.generate_json_response(
            system_prompt=prompt,
            messages=conversation,
            model=self.MODEL
        )

        return result

class InterviewJudgePanel:
    """
    Runs all judges and aggregates result
    """

    def __init__(self):
        self.technical = TechnicalJudge()
        self.behavioral = BehavioralJudge()
        self.structural = StructuralJudge()

    async def evaluate(self, conversation):
        tech = await self.technical.judge(conversation)
        beh = await self.behavioral.judge(conversation)
        struct = await self.structural.judge(conversation)

        overall_score = round(
            (tech["score"] + beh["score"] + struct["score"]) / 3, 2
        )

        return {
            "technical_score": tech["score"],
            "behavioral_score": beh["score"],
            "structural_score": struct["score"],
            "overall_score": overall_score,

            "technical_feedback": tech["feedback"],
            "behavioral_feedback": beh["feedback"],
            "structural_feedback": struct["feedback"],

            "improvement_areas": (
                tech["feedback"].get("weaknesses", []) +
                beh["feedback"].get("concerns", []) +
                struct["feedback"].get("needs_improvement", [])
            )
        }
