from django.contrib import admin
from .models import UserProficiency


@admin.register(UserProficiency)
class UserProficiencyAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "theta")
