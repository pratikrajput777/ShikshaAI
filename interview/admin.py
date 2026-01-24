from django.contrib import admin
from .models import (
    ConversationSession,
    InterviewTurn,
    InterviewEvaluation
)

admin.site.register(ConversationSession)
admin.site.register(InterviewTurn)
admin.site.register(InterviewEvaluation)
