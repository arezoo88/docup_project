"""docup_core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
# from django.shortcuts import redirect
from django.urls import path, include
from django.views.generic import RedirectView

from . import settings
from django.conf.urls import include, url
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
admin.site.site_header = "Neuronio Team"
admin.site.site_title = "Neuronio Admin"
admin.site.index_title = "Welcome to Server Portal"
urlpatterns = [
    url(r'^$', RedirectView.as_view(url='https://neuronio.ir'), name='main site'),
    url(r'^baton/', include('baton.urls')),
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/', include('follow_up.urls')),
    path('payment/', include('payment.urls')),
    path('medical-test/', include('medical_test.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('devices/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create', 'get': 'list'}), name='create_fcm_device'),
    path('document/',include('doc.urls'))

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
