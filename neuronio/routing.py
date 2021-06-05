from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing
from . import authToken

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': authToken.TokenAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})