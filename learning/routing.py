from django.urls import re_path
from . import consumers
  
websocket_urlpatterns = [
      re_path(r'ws/study-plan/progress/$', consumers.StudyPlanProgressConsumer.as_asgi()),
  ]

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import interview.routing
import learning.routing
import users.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            interview.routing.websocket_urlpatterns +
            learning.routing.websocket_urlpatterns +
            users.routing.websocket_urlpatterns
        )
    ),
})