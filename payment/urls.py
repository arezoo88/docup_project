from django.urls import path

from payment.views import *
urlpatterns = [
    path('transaction-call-back/<str:id>/', transaction_call_back),

]