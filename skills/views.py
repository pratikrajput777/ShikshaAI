from django.shortcuts import render

class OccupationViewSet(viewsets.ReadOnlyModelViewSet):
      queryset = Occupation.objects.all()
      serializer_class = OccupationSerializer
      
class SkillViewSet(viewsets.ReadOnlyModelViewSet):
      queryset = Skill.objects.all()
      serializer_class = SkillSerializer