from django.db import models

class Occupation(models.Model):
       esco_uri = models.CharField(max_length=255, unique=True, null=True, blank=True)
       onet_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
       preferred_label = models.CharField(max_length=255)
       alternative_labels = models.JSONField(default=list, blank=True)
       description = models.TextField(blank=True)
       parent = models.ForeignKey(
           "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
       )
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       class Meta:
           db_table = "occupations"
           indexes = [
               models.Index(fields=["preferred_label"]),
               models.Index(fields=["onet_code"]),
               models.Index(fields=["parent"]),
           ]

       def _str_(self) -> str:
           return self.preferred_label


class Skill(models.Model):
       TECHNICAL = "technical"
       SOFT = "soft"
       KNOWLEDGE = "knowledge"

       SKILL_TYPE_CHOICES = [
           (TECHNICAL, "Technical"),
           (SOFT, "Soft"),
           (KNOWLEDGE, "Knowledge"),
       ]

       esco_uri = models.CharField(max_length=255, unique=True, null=True, blank=True)
       preferred_label = models.CharField(max_length=255)
       alternative_labels = models.JSONField(default=list, blank=True)
       description = models.TextField(blank=True)
       skill_type = models.CharField(max_length=20, choices=SKILL_TYPE_CHOICES)
       prerequisites = models.ManyToManyField(
           "self", symmetrical=False, related_name="required_for", blank=True
       )
       embeddings = models.JSONField(default=list, blank=True)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       class Meta:
           db_table = "skills"
           indexes = [
               models.Index(fields=["preferred_label"]),
               models.Index(fields=["skill_type"]),
           ]

       def _str_(self) -> str:
           return self.preferred_label


class OccupationSkill(models.Model):
       occupation = models.ForeignKey(Occupation, on_delete=models.CASCADE)
       skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
       importance = models.FloatField(default=0.5)
       required_proficiency_theta = models.FloatField(default=0.0)

       class Meta:
           db_table = "occupation_skills"
           unique_together = ["occupation", "skill"]

       def _str_(self) -> str:
           return f"{self.occupation.preferred_label} requires {self.skill.preferred_label}"


class SkillEmbedding(models.Model):
       skill = models.OneToOneField(Skill, on_delete=models.CASCADE, related_name="embedding")
       vector = models.JSONField(default=list)
       model_name = models.CharField(max_length=100, default="text-embedding-004")
       created_at = models.DateTimeField(auto_now_add=True)

       class Meta:
           db_table = "skill_embeddings"

       def _str_(self) -> str:
           return f"Embedding for {self.skill.preferred_label}"