from rest_framework.routers import DefaultRouter
from .views import AssessmentViewSet
  
router = DefaultRouter()
router.register(r'assessment', AssessmentViewSet, basename='assessment')
  
urlpatterns = router.urls