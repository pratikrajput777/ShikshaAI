from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DiagnosticSession
from .services import AssessmentService
from .serializers import *
  
class AssessmentViewSet(viewsets.ViewSet):
      """Diagnostic assessment endpoints."""
      
      @action(detail=False, methods=['post'])
      def start(self, request):
          """Start new diagnostic session for a skill."""
          skill_id = request.data.get('skill_id')
          
          if not skill_id:
              return Response(
                  {'error': 'skill_id required'},
                  status=status.HTTP_400_BAD_REQUEST
              )
          
          session = AssessmentService.start_session(
              user=request.user,
              skill_id=skill_id
          )
          
          return Response(
              DiagnosticSessionSerializer(session).data,
              status=status.HTTP_201_CREATED
          )
      
      @action(detail=True, methods=['get'])
      def next_question(self, request, pk=None):
          """Get next adaptive question."""
          session = DiagnosticSession.objects.get(pk=pk, user=request.user)
          
          question = AssessmentService.get_next_question(session)
          
          if question is None:
              return Response({
                  'completed': True,
                  'final_theta': session.current_theta,
                  'final_se': session.current_se
              })
          
          return Response(QuestionBankSerializer(question).data)
      
      @action(detail=True, methods=['post'])
      def submit_answer(self, request, pk=None):
          """Submit answer to question."""
          session = DiagnosticSession.objects.get(pk=pk, user=request.user)
          
          serializer = AnswerSubmitSerializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          
          question = QuestionBank.objects.get(
              id=serializer.validated_data['question_id']
          )
          
          answer_log = AssessmentService.submit_answer(
              session=session,
              question=question,
              user_answer=serializer.validated_data['user_answer']
          )
          
          return Response({
              'correct': answer_log.is_correct,
              'theta_updated': answer_log.theta_after,
              'se': answer_log.se_after,
              'should_continue': not session.should_terminate
          })
      
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from skills.models import Occupation
from assessment.serializers import SkillGapSerializer
from assessment.services import AssessmentService

class AssessmentViewSet(ViewSet):

    @action(detail=False, methods=['get'])
    def skill_gaps(self, request):
        occupation_id = request.query_params.get('occupation_id')

        if not occupation_id:
            return Response(
                {"error": "occupation_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        occupation = Occupation.objects.get(id=occupation_id)

        gaps = AssessmentService.calculate_skill_gaps(
            user=request.user,
            target_occupation=occupation
        )

        serializer = SkillGapSerializer(gaps, many=True)
        return Response(serializer.data)
