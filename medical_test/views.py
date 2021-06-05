from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.errors import errors
from authentication.models import Patient, Doctor
from follow_up.models import Panel, Panel2CognitiveTest
from medical_test.models import CognitiveTest, PatientResponse, Question, Answer
from medical_test.serializers import CognitiveTestSerializerWithoutQA, CognitiveTestSerializerFull, \
    Panel2CognitiveTestSerializer, PatientResponseSerializer,AnsweredTestPanelSerializer,AnsweredTestSerializer
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN,HTTP_500_INTERNAL_SERVER_ERROR
from authentication.permissions import IsAdminOrOwner
from follow_up.tasks import send_async_notification
from datetime import datetime
from django.db.models import Q
from follow_up.models import  ScreeningSteps

def calculate_age(date):
    b_date = datetime.strptime(date, '%Y-%m-%d')
    return "%d" % ((datetime.today() - b_date).days/365)


class CognitiveTestsList(generics.ListAPIView):
    """
        get list of tests that are enable
    """
    serializer_class = CognitiveTestSerializerWithoutQA
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        user = self.request.user
        queryset = CognitiveTest.objects.filter(enabled=True,)

        # if user.type == 0:
        #     patient = get_object_or_404(Patient, user=user)
            # if patient.date_of_birth:
            #     if int(calculate_age(str(patient.date_of_birth)))>50:
            #         queryset = queryset.filter(~Q(name='تست PHQ'))
            #     else:
            #         queryset = queryset.filter(~Q(name='تست GDS'))
        return queryset


class CognitiveTestsRetrieve(generics.RetrieveAPIView):
    """
        get test info with id
    """
    serializer_class = CognitiveTestSerializerFull
    permission_classes = (IsAuthenticated,)
    queryset = CognitiveTest
    lookup_field = 'id'


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrOwner])
def get_patient_response_of_a_test(request): #get panel_id is better than patient_id
    try:
        serializer_class = CognitiveTestSerializerFull
        test_id = request.query_params.get('test_id')
        patient_id = request.query_params.get('patient_id')

        screening_step_id = request.query_params.get('screening_step_id')
        if not screening_step_id:
            screening_step_id = None
        # panel_cognitive_test_id = request.query_params.get('panel_cognitive_test_id')
        # patient_id = request.query_params.get('patient_id')
        if not test_id :
            return Response(status=HTTP_403_FORBIDDEN, data={'msg': errors[613], 'code': "613"})

        try:
            patient = get_object_or_404(Patient, pk=patient_id)
        except:
            patient = None
        # if (patient.user.id != request.user.id and request.user.type == 0):
        #     return Response(status=HTTP_403_FORBIDDEN, data={'msg': errors[617], 'code': "617"})

        queryset = CognitiveTest.objects.filter(id=test_id)
        if len(queryset) == 0:
            return Response(status=HTTP_403_FORBIDDEN, data={'msg': errors[618], 'code': "618"})
        query_set = serializer_class(queryset, many=True)
        # if panel_cognitive_test_id:
        #     query = Panel2CognitiveTest.objects.filter( CognitiveTest=test_id, id=panel_cognitive_test_id)[0]
        if screening_step_id:
            responses = PatientResponse.objects.filter(CognitiveTest=test_id, screening_step=screening_step_id)
        else:
            responses = PatientResponse.objects.filter(CognitiveTest=test_id, screening_step=screening_step_id,patient=patient)
        query_set = query_set.data[0]
        if len(responses) == 0:
            query_set['status'] = '0'
            return Response(query_set)

        query_set['status'] = '1'

        patient_serializer = PatientResponseSerializer(responses, many=True)
        for index_q, question in enumerate(query_set['questions']):
            for index_pr, response in enumerate(patient_serializer.data):
                if response['question'] == question['id']:
                    if len(question['answers']) == 0:
                        query_set['questions'][index_q]['description'] =response['description']
                        continue
                    for index_a, answer in enumerate(question['answers']):
                        if response['Answer'] == answer['id']:
                            query_set['questions'][index_q]['answers'][index_a]['selected'] = "selected"
                            continue
                    continue
        return Response(query_set)
    except:
        import traceback
        print(444,traceback.format_exc())

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_new_cognitive_test_to_patient_panel(request):
    test_id = request.query_params.get('test_id')
    patient_id = request.query_params.get('patient_id')
    if not test_id or not patient_id: raise PermissionDenied({'msg': errors[613], 'code': 613})
    if not request.user.type == 1:  # only doctor can send test into patient panel
        raise PermissionDenied({'msg': errors[612], 'code': 612})
    test = get_object_or_404(CognitiveTest, id=test_id)
    doctor = get_object_or_404(Doctor, user=request.user)

    panel = get_object_or_404(Panel, doctor=doctor, patient=patient_id)
    # if len(Panel2CognitiveTest.objects.filter(CognitiveTest=test, panel=panel))!=0:
    #     Panel2CognitiveTest.objects.filter(CognitiveTest=test, panel=panel).update(done=False,time_add_test=datetime.now())
    # else:
    panel_cognitive_test_id = Panel2CognitiveTest.objects.create(CognitiveTest=test, panel=panel)
    patient = get_object_or_404(Patient, pk=patient_id)
    body_info = f'نام دکتر: {doctor.user.first_name} {doctor.user.last_name}'

    title = f'درخواست پاسخ گویی به {test}'

    send_async_notification.apply_async(
        args=(title, body_info, patient.user.id,{"type": 2, "payload": {'panel_id': panel.id,'panel_cognitive_test_id':panel_cognitive_test_id.pk,"title":test.name, 'doctor_id': doctor.id, 'patient_id': patient_id, 'test_id': test_id}},datetime.now(),2))

    return Response(status=HTTP_200_OK, data={"msg": "تست با موفقیت برای سلامت جو ارسال شد."})




class CognitiveTestOfPanel(generics.ListAPIView):
    serializer_class = AnsweredTestPanelSerializer
    permission_classes = (IsAuthenticated,)
    def get_queryset(self):
        # self.check_permission()
        # docs = Panel2CognitiveTest.objects.order_by('time_add_test')
        docs = Panel2CognitiveTest.objects.filter(Q(panel__doctor__user=self.request.user)| Q(panel__patient__user=self.request.user))
        docs = docs.order_by('time_add_test')
        panel_id = self.request.query_params.get('panel_id')
        done = self.request.query_params.get('done')
        # if (patient.user.id != self.request.user.id and  self.request.user.is_staff == False):
        #     return Response(status=HTTP_403_FORBIDDEN, data={'msg': errors[617], 'code': "617"})
        if panel_id:
            docs = docs.filter(panel=panel_id)
        if done:
            docs = docs.filter(done=done)
        return docs





def save_response(questions,cgtest,patient,screening_step_id,):
        for info in questions:
            question = get_object_or_404(Question, pk=info["question_id"])
            if "answer_id" in info :
                answer = get_object_or_404(Answer, pk=info["answer_id"], question=question)
            else:
                answer = None
            if "desc" in info:
                desc = info["desc"]
            else:
                desc = None
            if len(PatientResponse.objects.filter(
                    CognitiveTest=cgtest,
                    question=question,screening_step=screening_step_id,patient=patient)) == 0:

                response = PatientResponse(Answer=answer,
                                           CognitiveTest=cgtest,
                                           question=question,
                                           description=desc,
                                           patient=patient,
                                           screening_step=screening_step_id
                                           )

                response.save()
            else:
                PatientResponse.objects.filter(
                    CognitiveTest=cgtest,
                    patient=patient,
                    question=question,screening_step=screening_step_id

                ).update(Answer=answer,description=desc)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_patient_response_of_a_test(request):# TODO rollback check shavad
    try:
        if request.user.type != 0:
            raise PermissionDenied({'msg': errors[604], 'code': 604})
        cognitive_test_id = request.data.get('cognitive_test_id')
        questions = request.data.get('questions')
        patient = get_object_or_404(Patient, user_id=request.user.id)
        if not cognitive_test_id or not questions:
            return Response(status=HTTP_403_FORBIDDEN, data={'msg': errors[616], 'code': "616"})
        cgtest = get_object_or_404(CognitiveTest, pk=cognitive_test_id)
        screening = None
        if request.data.get('screening_step_id'):
            screening_step_id = request.data.get('screening_step_id')
            screening = get_object_or_404(ScreeningSteps, pk=screening_step_id)
            for key, value in screening.tests_response_status.items():
                if key == str(cognitive_test_id):
                    screening.tests_response_status[key] = True
                    screening.save()
                    continue
        save_response(questions,cgtest,patient,screening_step_id=screening)
        return Response(status=HTTP_200_OK, data={"msg": "نتیجه با موفقیت ذخیره شد."})
    except:
         import traceback
         return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": "سرور با خطا مواجه شده است."})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def update_test_status(request):#when open test by patient it seems is responsed!
    test_id = request.query_params.get('test_id')
    screening_step_id = request.query_params.get('screening_step_id')
    screening = get_object_or_404(ScreeningSteps, pk=screening_step_id)
    if screening.tests_response_status[str(test_id)] ==False:
        screening.tests_response_status[str(test_id)] = True
        screening.save()
        return Response({'success': True})
    else:
        return Response({'success': False})
