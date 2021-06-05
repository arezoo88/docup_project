from django.urls import path

from follow_up.views import *
from utils.utils import get_version

urlpatterns = [
    path('get-discount/',get_discount),#done
    path('ica/',IcaCreate.as_view()),#check
    path('get-ica/',IcaRetrieveUpdate.as_view()),#check
    path('get-screening-plan/<int:clinic_id>/', RetrieveScreening.as_view()),
    path('screening/', check_user_has_active_screening),
    path('activate-screening-plan/', activate_screening),
    path('set-doctor/', set_doctor),
    path('buy-screening-plan/', buy_screening_with_credit),
    path('panels/', PanelsListCreate.as_view()),
    path('brief-panels/', PanelsListCreateJustIdAndTitleOfSub.as_view()),
    path('panels/<int:contact_id>/', RetrievePanel.as_view()),
    path('create-file/<int:list_id>/', CreateFile.as_view()),
    path('update-image/<int:pk>/', UpdateImage.as_view()),#done
    path('delete-file/<int:pk>/', DeleteFile.as_view()),
    path('retrieve-file-list/<int:pk>/', RetrieveImageList.as_view()),#done
    path('update-answer/<int:pk>/', UpdateDQAnswer.as_view()),
    path('patients/<int:pk>/', RetrievePatient.as_view()),
    path('doctors/<int:pk>/', RetrieveDoctor.as_view()),
    path('clinics/<int:pk>/', RetrieveClinic.as_view()),
    path('search/doctors/', SearchDoctors.as_view()),
    path('on-call-doctors/', OnlineDoctors.as_view()),
    path('search/clinics/', SearchClinics.as_view()),
    path('search/patients/', SearchPatients.as_view()),
    path('search/patients-list/', SearchPatientsJustNameAndIDAndAvatar.as_view()),
    path('visits/', VisitListCreate.as_view()),
    path('history/', DoctorListHistory.as_view()),
    path('on-call-visit/', on_call_visit),
    path('visits/<int:id>/', VisitRetrieveUpdateDestroy.as_view()),
    path('visit-related/<int:id>/', VisitRelatedRetrieve.as_view()),
    path('visit-related-accepted/<int:id>/', VisitRelatedRetrieveAccepted.as_view()),
    path('visit-related-accepted-nearest/<int:id>/', VisitRelatedRetrieveAcceptedNearest.as_view()),
    path('response-visit/<int:id>/', ResponseVisit.as_view()),
    path('my-doctors/', MyDoctors.as_view()),
    path('my-disease-images/', MyDiseaseImages.as_view()),
    path('doctor-plan/', RetrieveUpdateDoctorSupport.as_view()),
    path('doctor-plan/<int:id>', RetrieveDoctorSupport.as_view()),
    path('agora-channel-name/', get_agora_channel_name),
    path('newest-notifications/', NotificationListUpdate.as_view()),
    path('patient-tracking/', patient_tracking),
    path('get-all-patient-detailed/<int:id>/', get_all_patient_detailed),
    path('bank/', LogoBankListCreate.as_view()),#done
    path('text-plan-visit/', VisitPlanCreate.as_view()),
    path('deactive-or-active-chat/<int:id>/', TerminateChat.as_view()),
    path('get-version/', get_version),#done

]