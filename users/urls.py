from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import UserViewSet
from .auth_views import login_view, register_view, logout_view, me_view


router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("auth/login/", login_view, name="login"),
    path("auth/register/", register_view, name="register"),
    path("auth/logout/", logout_view, name="logout"),
    path("auth/me/", me_view, name="me"),
] + router.urls


