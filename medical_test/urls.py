from django.urls import path

from medical_test.views import *
urlpatterns = [
    path('available-tests/', CognitiveTestsList.as_view()),#done
    path('available-tests/<int:id>/', CognitiveTestsRetrieve.as_view()),#done
    path('send-test-to-patient/', add_new_cognitive_test_to_patient_panel),#done
    path('cognitive-tests-panel/', CognitiveTestOfPanel.as_view()),#done
    path('cognitive-tests-response/', get_patient_response_of_a_test),#done
    path('cognitive-tests-add-response/', save_patient_response_of_a_test),#done
    path('update-status/', update_test_status)#done
]