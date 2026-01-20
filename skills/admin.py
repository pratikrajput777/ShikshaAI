from django.contrib import admin
from .models import Occupation, Skill

# Unregister if already registered
for model in [Occupation, Skill]:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

@admin.register(Occupation)
class OccupationAdmin(admin.ModelAdmin):
      list_display = ('preferred_label', 'onet_code', 'parent')
      search_fields = ('preferred_label', 'onet_code')
  
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
      list_display = ('preferred_label', 'skill_type')
      list_filter = ('skill_type',)
      search_fields = ('preferred_label',)