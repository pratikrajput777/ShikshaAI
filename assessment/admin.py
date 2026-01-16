from django.contrib import admin
from assessment.models import SkillGap

@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'skill',
        'occupation',
        'current_level',
        'required_level',
        'priority_score',
        'addressed'
    )
    list_filter = ('occupation', 'addressed')
    search_fields = ('user__username', 'skill__name')
