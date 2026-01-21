from django.contrib import admin
from .models import (
    StudyPlan,
    LearningModule,
    Lesson,
    CFUQuiz,
    CFUAttempt,
    Remediation
)

admin.site.register(StudyPlan)
admin.site.register(LearningModule)
admin.site.register(Lesson)
admin.site.register(CFUQuiz)
admin.site.register(CFUAttempt)
admin.site.register(Remediation)
