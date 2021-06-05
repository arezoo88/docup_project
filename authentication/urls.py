from django.urls import path
from authentication.views import *

urlpatterns = [
    path('log-in/', log_in),
    path('verify/', Verification.as_view()),
    path('doctor/', DoctorProfile.as_view()),
    path('patient/', PatientProfile.as_view()),
    path('clinic/', ClinicProfile.as_view()),
    path('suggest-doctor/', SuggestedDoctorCreate.as_view()),
    path('upload-profile-image/<int:pk>', UploadProfileImage.as_view()),
]
