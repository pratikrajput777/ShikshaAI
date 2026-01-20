from rest_framework import serializers
from .models import DiagnosticSession, QuestionBank, AnswerLog
  
class QuestionBankSerializer(serializers.ModelSerializer):
      class Meta:
          model = QuestionBank
          fields = ['id', 'question_text', 'options']
          # Don't expose correct_answer or IRT params to client
  
class DiagnosticSessionSerializer(serializers.ModelSerializer):
      skill_name = serializers.CharField(source='skill.preferred_label', read_only=True)
      
      class Meta:
          model = DiagnosticSession
          fields = ['id', 'skill', 'skill_name', 'current_theta', 
                   'current_se', 'question_count', 'status', 
                   'started_at', 'completed_at']
          read_only_fields = ['current_theta', 'current_se', 'question_count']
  
class AnswerSubmitSerializer(serializers.Serializer):
      question_id = serializers.IntegerField()
      user_answer = serializers.IntegerField(min_value=0, max_value=3)
