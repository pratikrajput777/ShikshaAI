from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
       target_role = models.CharField(max_length=255, blank=True)
       experience_years = models.PositiveIntegerField(default=0)
       learning_style = models.CharField(
           max_length=50,
           blank=True,
           help_text="e.g. visual, auditory, kinesthetic",
       )
       
       # Use email as the unique identifier for authentication
       USERNAME_FIELD = 'email'
       REQUIRED_FIELDS = ['username']  # username is still required but not used for login
       
       # Make email unique
       email = models.EmailField(unique=True)

       class Meta:
           db_table = "users"
           indexes = [
               models.Index(fields=["username"]),
               models.Index(fields=["email"]),
               models.Index(fields=["target_role"]),
           ]

       @property
       def readiness_score(self) -> int:
           """Placeholder readiness score; refined by later days."""
           return 0
       
class UserProficiency(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    skill = models.ForeignKey("skills.Skill", on_delete=models.CASCADE)
    theta = models.FloatField()
    standard_error = models.FloatField()
    calibration_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "skill")



class UserSkill(models.Model):
       user = models.ForeignKey("users.User", on_delete=models.CASCADE)
       skill = models.ForeignKey("skills.Skill", on_delete=models.CASCADE)
       self_assessment = models.CharField(max_length=50, blank=True)
       created_at = models.DateTimeField(auto_now_add=True)

       class Meta:
           db_table = "user_skills"
           unique_together = ["user", "skill"]