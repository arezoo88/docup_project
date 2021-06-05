from django.urls import path

from chat.views import *

urlpatterns = [
    path('messages/<int:panel_id>/', SendMessageToPanel.as_view()),
    path('setlastseen/<int:panel_id>/', SendLastSeen.as_view()),
]
