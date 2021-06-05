import logging
import os

import jwt, re
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.conf import LazySettings
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from urllib import parse

from rest_framework.generics import get_object_or_404

from authentication.models import User

logger = logging.getLogger("test")
settings = LazySettings()


@database_sync_to_async
def get_user(username):
    user = get_object_or_404(User, username=username)

    try:
        user = get_object_or_404(User, username=username)

        return user
    except User.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self)


class TokenAuthMiddlewareInstance:
    """
    Yeah, this is black magic:
    https://github.com/django/channels/issues/1399
    """

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        keyword, query = parse.parse_qs(self.scope['query_string'].decode("utf-8"))['Authorization'][0].split()
        # print(query)
        # scope=self.scope
        if query:
            print("ssssss")

            user_jwt = jwt.decode(
                query,
                settings.SECRET_KEY,
            )
            # os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
            print("ssssss")
            print(user_jwt)
            # print( User.objects.all().count())
            # usr =  get_object_or_404(User, username=user_jwt["username"])
            self.scope['user'] = await get_user(user_jwt["username"])
            # os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "false"
            # print(usr)
            print("salam sadegh")
            # scope['user'] = usr
            # scope['username'] = user_jwt["username"]

            # AnonymousUser()

        inner = self.inner(self.scope)
        return await inner(receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))
