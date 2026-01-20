from django.contrib import admin
from users.models import User, UserProficiency, UserSkill
from skills.models import Occupation, Skill


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
       list_display = ("username", "email", "target_role", "is_active")
       search_fields = ("username", "email")


@admin.register(UserProficiency)
class UserProficiencyAdmin(admin.ModelAdmin):
       list_display = ("user", "skill", "theta", "standard_error")
       search_fields = ("user_username", "skill_preferred_label")

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
       list_display = ("user", "skill", "self_assessment", "created_at")


@admin.register(Occupation)
class OccupationAdmin(admin.ModelAdmin):
       list_display = ("preferred_label", "onet_code", "parent")
       search_fields = ("preferred_label", "onet_code")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
       list_display = ("preferred_label", "skill_type")
       list_filter = ("skill_type",)
       search_fields = ("preferred_label",)