from datetime import timedelta
from django.db.models import Q, F
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django_filters.rest_framework import DjangoFilterBackend
from fcm_django.models import FCMDevice
from rest_framework import generics, viewsets, status,mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from authentication.models import Doctor, Patient, Clinic,ClinicPlan, DoctorSupports, User, WorkTime, WorkDay,VisitType
from chat.consumers import ChatConsumer
from chat.models import ChatMessage
from chat.serializers import MessageSerializer
from authentication.serializers import UserSerializer
from follow_up.models import Panel, DQAnswer, Ticket, Visit, HealthEvent, Drug, Article, BankLogo,VisitPlan,Screening,ScreeningSteps,Ica
from follow_up.serializers import PanelSerializer, BriefDoctorSupportsSerializerWithReserveVisit, DQAnswerSerializer, \
    BriefPatientsSerializer, TicketSerializer, BriefDoctorSerializerWithoutPanels, \
    VisitSerializer, BriefClinicSerializer,ClinicSerializerwithIdAndAddress, PatientSerializer, DoctorSerializer, BriefClinicSerializerWithFullServices, \
    HealthEventSerializerWithInvitedIDs, HealthEventSerializerWithoutIds, HealthEventSerializerWithoutPatientsDocs, \
    DrugSerializer, NotificationSerializer,VisitPlanSerializer, \
    BriefPatientsSerializerJustIdNameAvatar, HealthEventSerializerJustIdAndNameForParticipates,BriefDoctorSerializerWithoutClinicAndPanels, \
    BriefDrugSerializer, BriefPatientsSerializerJustIdAndNameAndAvatar, DrugSerializerWithoutPatientAndDoctor, \
    PanelSerializerWithoutDoctor, DoctorSupportsSerializer, BriefDoctorSupportsSerializer, ArticleSerializer, \
    PanelSerializerJustIdAndTitleOfSubTypes, PanelSerializerJustPatientIdNameStatus, WorkTimeSerializer, WorkDaySerializer, \
    VisitSerializerWithUsers, BankLogoSerializer, Notification,VisitTypeSerializerFull,ScreeningSerializer,ScreeningStepsSerializer,IcaSerializer
from follow_up.tasks import send_async_notification, async_auto_reject_visit, async_auto_recall_doctor_to_answer, \
    async_auto_recall_visit, async_auto_recall_participates,auto_disable_screening
from follow_up.utils import get_relevant_health_events_queryset, get_patient_drugs, search_my_relevant_patient_panels, \
    get_my_partner_panel, refund_transaction, check_transaction_possibility, get_relevant_visit_queryset, \
    check_interference, charge_doctor, get_relevant_visit_queryset_pending,check_transaction_possibility_plan
from utils.models import Image, ImageList,Voucher
from utils.serializers import ImageSerializer, ImageListSerializer
from utils.utils import full_panel_with_dynamic_fields
from random import randint
from django.forms.models import model_to_dict
from utils.errors import errors
from synapps.views import save_patient_info_in_synapps
from medical_test.serializers import CognitiveTestSerializerWithoutQA
from medical_test.models import CognitiveTest
import json



class IcaCreate(generics.CreateAPIView,generics.UpdateAPIView):
    serializer_class = IcaSerializer
    permission_classes = (IsAuthenticated,)

    def check_permission(self):
        user = self.request.user
        if user.type == 0:
            raise PermissionDenied()
        screening_step_obj = get_object_or_404(ScreeningSteps,pk=self.request.data.get('screening_step'))
        ica = get_object_or_404(Ica, screening_step=screening_step_obj)
        self.ica = ica

    def perform_create(self, serializer):
        user = self.request.user
        if user.type == 0:
            raise PermissionDenied()
        screening_step_obj = get_object_or_404(ScreeningSteps,pk=self.request.data.get('screening_step'))
        ica = Ica.objects.filter(screening_step=screening_step_obj)
        if len(ica) != 0:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=self.request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        serializer.save()

    def get_object(self):
        self.check_permission()
        return self.ica



    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance ,data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     return Response(serializer.data)



class IcaRetrieveUpdate(generics.RetrieveUpdateAPIView):
    serializer_class = IcaSerializer
    permission_classes = (IsAuthenticated,)

    def check_permission(self):
        user = self.request.user
        if user.type == 0:
            raise PermissionDenied()
        screening_step_id = self.request.query_params.get('screening_step_id')
        screening_step_obj = ScreeningSteps.objects.filter(pk=screening_step_id)
        if len(screening_step_obj)==0:
             raise NotFound({})

        else:
            ica = get_object_or_404(Ica, screening_step=screening_step_obj[0])
            self.ica = ica

    def get_object(self):
        self.check_permission()
        return self.ica


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_discount(request):# this method get discount percent base on code
    discount_code = request.query_params.get('code')
    if not discount_code:  raise PermissionDenied({'msg': errors[623], 'code': 623})

    get_percent = Voucher.objects.filter(code=discount_code,enabled=True)
    if len(get_percent)!=0:
        return Response({'success':True,'percent':get_percent[0].discount/100})
    else:
        return Response({'success':False,'percent':0})




class RetrieveScreening(generics.RetrieveAPIView): # get screening with clinic_id
    serializer_class = ScreeningSerializer
    permission_classes = (IsAuthenticated,)
    def get_object(self):
        clinic_id = self.kwargs['clinic_id']
        return get_object_or_404(Screening,clinic_id=clinic_id,enabled=True)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_has_active_screening(request, *args, **kwargs):
    try:
        # screening_steps = ScreeningSteps.objects.filter(patient__user=request.user,panel__doctor__clinic_id=4)
        panel_id = request.query_params.get('panel_id')
        if request.user.type == 0:
            screening_steps = ScreeningSteps.objects.filter(patient__user=request.user)
        else:
            screening_steps = ScreeningSteps.objects.filter(panel__id=panel_id)

        screening_steps_doctor = screening_steps.filter(~Q(panel=None))
        doctor = None
        clinic_info = None
        clinic_doctor_info = None
        if len(screening_steps_doctor)!=0:
            queryset = Doctor.objects.filter(id=screening_steps_doctor[0].panel.doctor.id)
            serializer = BriefDoctorSerializerWithoutClinicAndPanels(queryset, many=True)
            data = serializer.data
            null = None
            doctor = eval(json.dumps(data))[0]


        status_steps = {}
        if len(screening_steps) == 0:
            inactive_screening_steps = []
            active_screening_steps = []
        else:
            inactive_screening_steps = screening_steps.filter(enabled = False)
            active_screening_steps = screening_steps.filter(enabled = True)

            if len(active_screening_steps)!=0:
                actives = active_screening_steps[0]

                clinic_serializer = ClinicSerializerwithIdAndAddress
                queryset = Clinic.objects.get(pk=actives.screening.clinic.id)
                clinic_info = clinic_serializer(queryset)
                null = None
                clinic_info = eval(json.dumps(clinic_info.data))
                user_ = User.objects.get(id=actives.screening.clinic.user.id)
                queryset = Doctor.objects.filter(user=user_)
                serializer = BriefDoctorSerializerWithoutClinicAndPanels(queryset, many=True)
                data = serializer.data
                clinic_doctor_info = eval(json.dumps(data))[0]

                # actives = active_screening_steps[0]
                # queryset = Doctor.objects.filter(id=actives.panel.doctor.id)
                # serializer = BriefDoctorSerializerWithoutClinicAndPanels(queryset, many=True)
                # data = serializer.data
                # null =None
                # doctor = eval(json.dumps(data))[0]
                dict_tests = {}

                for key,value in actives.tests_response_status.items():
                    queryset = CognitiveTest.objects.filter(id =key )
                    serializer = CognitiveTestSerializerWithoutQA(queryset, many=True)
                    data = serializer.data
                    dict_tests[key] = {'status':value,'info':eval(json.dumps(data))[0]}

                status_steps = {'screening_step_id':actives.id,'payment_status':actives.payment_status,
                                'tests_response_status':dict_tests,
                                'ica_status':actives.ica_status,
                                'visit_status':actives.visit_status,

                                }
        status_steps['doctor_info'] = doctor
        status_steps['clinic_info'] = clinic_info
        status_steps['clinic_doctor_info'] = clinic_doctor_info
        return Response({'success': True, 'inactive': len(inactive_screening_steps), 'active': len(active_screening_steps),'status_steps':status_steps})
    except:
        import traceback
        print(traceback.format_exc())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_screening(request):
    user = request.user
    # screening_steps = ScreeningSteps.objects.filter(patient__user=request.user,panel__doctor__clinic_id=4,enabled=True)
    screening_steps = ScreeningSteps.objects.filter(patient__user=request.user,enabled=True)
    if len(screening_steps)>0:
        return Response({'success':False,'msg': errors[625], 'code': "625"})

    else:

        patient = get_object_or_404(Patient, user=user)
        screening_id = request.data.get('screening_id')
        # discount_code = request.data.get('code')
        # screening_id = request.query_params.get('screening_id')
        get_obj=None
        # get_percent = Voucher.objects.filter(code=discount_code,enabled=True)
        # percent = 0
        # if len(get_percent) != 0:
        #     get_obj = get_percent[0]
        #     percent = get_obj.discount / 100
        screening = get_object_or_404(Screening, pk=screening_id)

        # patient_user = patient.user
    # if patient_user.credit >=(screening.price-screening.price*percent):
    #     if len(get_percent)!=0:
    #         get_obj.expire_date=datetime.now()
    #         get_obj.enabled=False
    #         get_obj.save()
    #     random_doctor = get_object_or_404(Doctor.objects.filter(enabled=True, clinic_id=4).order_by('?')[:1])
    #     clinic_credit = get_object_or_404(User,username='Neuronio')
        # random_doctor_user = random_doctor.user
        tests = screening.medical_tests.all().values('id')
        dict_tests = {}
        for test in tests:
            value = test['id']
            dict_tests[value] = False
        # patient_user.credit =int(patient_user.credit )- (screening.price-(screening.price)*percent)
        # patient_user.save()
        # clinic_credit.credit =int(clinic_credit.credit)+ (screening.price-(screening.price)*percent)

        # clinic_credit.save()

        # panel, created = Panel.objects.get_or_create(patient=patient, doctor=random_doctor)

        serializer = ScreeningStepsSerializer(data={'payment_status': True})
        serializer.is_valid(raise_exception=True)

        serializer.save(panel=None, patient=patient,screening=screening,payment_type=0,tests_response_status=dict_tests,discount=get_obj)
        synapps_info = {'first_name': user.first_name, 'last_name': user.last_name,
                        # 'birth_location': patient.birth_location,
                        'username': user.username,
                        'gender': patient.gender,
                        'national_id': user.national_id,
                        # 'city': patient.city

                        }
        save_patient_info_in_synapps(synapps_info)

        return Response({'success':True,'msg': '', 'code': ""})
    # else:
        # return Response({'success':False,'msg': errors[624], 'code': "624"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_doctor(request):
    user = request.user
    patient = get_object_or_404(Patient, user=user)

    doctor_id = request.data.get('doctor_id')
    screening_step_id = request.data.get('screening_step_id')
    if doctor_id:
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        panel,created = Panel.objects.get_or_create(patient=patient, doctor=doctor)

    else:
        random_doctor = get_object_or_404(Doctor.objects.filter(enabled=True, clinic_id=4).order_by('?')[:1])
        panel ,created= Panel.objects.get_or_create(patient=patient, doctor=random_doctor)

    ScreeningSteps.objects.filter(pk=screening_step_id).update(panel=panel)
    return Response({'success':True})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_screening_with_credit(request):
    try:
        user = request.user
        screening_steps = ScreeningSteps.objects.filter(panel__patient__user=request.user,panel__doctor__clinic_id=4,enabled=True)
        if len(screening_steps)>0:
            return Response({'success':False,'msg': errors[625], 'code': "625"})

        else:

            patient = get_object_or_404(Patient, user=user)
            screening_id = request.data.get('screening_id')
            discount_code = request.data.get('code')
            # screening_id = request.query_params.get('screening_id')
            get_obj=None
            get_percent = Voucher.objects.filter(code=discount_code,enabled=True)
            percent = 0
            if len(get_percent) != 0:
                get_obj = get_percent[0]
                percent = get_obj.discount / 100
            screening = get_object_or_404(Screening, pk=screening_id)

            patient_user = patient.user
        if patient_user.credit >=(screening.price-screening.price*percent):
            if len(get_percent)!=0:
                get_obj.expire_date=datetime.now()
                get_obj.enabled=False
                get_obj.save()
            # random_doctor = get_object_or_404(Doctor.objects.filter(enabled=True, clinic_id=4).order_by('?')[:1])
            clinic_credit = get_object_or_404(User,username='09014284966')
            # random_doctor_user = random_doctor.user
            tests = screening.medical_tests.all().values('id')
            dict_tests = {}
            for test in tests:
                value = test['id']
                dict_tests[value] = False
            patient_user.credit =int(patient_user.credit )- (screening.price-(screening.price)*percent)
            patient_user.save()
            clinic_credit.credit =int(clinic_credit.credit)+ (screening.price-(screening.price)*percent)

            clinic_credit.save()

            # panel, created = Panel.objects.get_or_create(patient=patient, doctor=random_doctor)

            serializer = ScreeningStepsSerializer(data={'payment_status': True})
            serializer.is_valid(raise_exception=True)
            serializer.save(panel=None, patient=patient, screening=screening, payment_type=0, tests_response_status=dict_tests, discount=get_obj)

            # serializer.save(panel=None, screening=screening,payment_type=0,tests_response_status=dict_tests,discount=get_obj)
            synapps_info = {'first_name': user.first_name, 'last_name': user.last_name,
                            # 'birth_location': patient.birth_location,
                            'username': user.username,
                            'gender': patient.gender,
                            'national_id': user.national_id,
                            # 'city': patient.city

                            }
            save_patient_info_in_synapps(synapps_info)
            print(4444)
            return Response({'success':True,'msg': '', 'code': ""})
        else:
            return Response({'success':False,'msg': errors[624], 'code': "624"})
    except:
        import traceback
        print(444,traceback.format_exc())



class MyDiseaseImages(generics.ListAPIView):
    serializer_class = ImageListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        panels = Panel.objects.all()
        panels = panels.filter(patient__user=self.request.user).order_by('-modified_date')

        return [p.disease_images for p in panels]


class MyDoctors(generics.ListAPIView):  # my-doctors/   list of doctors that patient have panel with them
    serializer_class = BriefDoctorSerializerWithoutPanels
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        panels = Panel.objects.all()
        panels = panels.filter(patient__user=self.request.user).order_by('-modified_date')

        return [p.doctor for p in panels]


class SearchDoctors(generics.ListAPIView):  # search/doctors/  search doctors in this method
    serializer_class = BriefDoctorSerializerWithoutPanels
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        query = self.request.query_params.get('query')
        expertise = self.request.query_params.get('expertise')
        clinic_id = self.request.query_params.get('clinic_id')
        docs = Doctor.objects.filter(enabled=True)

        if query:
            # expertises = []
            # if expertises is not None:
            #     for exp in query.split(','):
            #         expertises.append(str(exp))
            docs = docs.filter(
                Q(user__last_name__contains=query) | Q(user__first_name__contains=query)).order_by('-created_date')
        if expertise:
            docs = docs.filter(expert__contains=expertise)
        if clinic_id:
            docs = docs.filter(clinic=clinic_id)
        if len(docs) != 0:
            docs = docs.order_by('user__last_name')
        return docs


class OnlineDoctors(generics.ListAPIView):
    serializer_class = BriefDoctorSerializerWithoutPanels
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """ doctors that have online field bigger than 0 are online"""
        docs = Doctor.objects.filter(user__online__gt=0, expert__contains="عمومی")
        return docs


class SearchClinics(generics.ListAPIView):
    serializer_class = BriefClinicSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        name = self.request.query_params.get('name')
        sub_type = self.request.query_params.get('sub_type')
        clinics = Clinic.objects.all()
        if name: clinics = clinics.filter(clinic_name__contains=name).order_by('-created_date')
        if sub_type: clinics = clinics.filter(sub_type=sub_type).order_by('-created_date')
        return clinics


class SearchPatients(generics.ListAPIView):
    serializer_class = PanelSerializerWithoutDoctor
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        query = self.request.query_params.get('query')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        return search_my_relevant_patient_panels(self.request.user, query, from_date, to_date)


class SearchPatientsJustNameAndIDAndAvatar(generics.ListAPIView):  # search/patients-list/  list of patient for doctor
    serializer_class = PanelSerializerJustPatientIdNameStatus
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        query = self.request.query_params.get('query')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        status_s = self.request.query_params.get('status')
        searching_statuses = []
        if status_s is not None:
            for status_ in status_s.split(','):
                searching_statuses.append(int(status_))
        panels = search_my_relevant_patient_panels(self.request.user, query, from_date, to_date, searching_statuses)
        return panels


class PanelsListCreate(generics.ListCreateAPIView):
    serializer_class = PanelSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.type == 0:
            return Panel.objects.filter(patient__user=user).order_by('-created_date')
        else:
            return Panel.objects.filter(doctor__user=user).order_by('-created_date')

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_staff: raise PermissionDenied({'detail': "u are not staff", "error_code": 605})
        serializer.save()


class PanelsListCreateJustIdAndTitleOfSub(generics.ListAPIView):
    serializer_class = PanelSerializerJustIdAndTitleOfSubTypes
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.type == 0:
            return Panel.objects.filter(patient__user=user).order_by('-created_date')
        else:
            return Panel.objects.filter(doctor__user=user).order_by('-created_date')


class RetrievePanel(generics.RetrieveUpdateDestroyAPIView):
    queryset = Panel.objects.all()
    serializer_class = PanelSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        contact_id = self.kwargs['contact_id']
        user = self.request.user
        return get_my_partner_panel(user, contact_id)


class DoctorListHistory(generics.ListAPIView):
    serializer_class = VisitSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        me = get_object_or_404(Doctor, user=user)
        return Visit.objects.filter(doctor=me, status__in=[1, 2]).order_by('-request_visit_time')


def check_plan_feasibility(doctor,visit_type,visit_duration_plan):
    plan = doctor.plan
    duration = {
        0:'0',
        1:'1',
        2:'2',
    }
    visit= VisitType.objects.filter(Doctor_supports=plan,visit_type=visit_type)
    if len(visit) == 0:
        return False
    visit_duration_plan_exists = visit[0].visit_duration_plan

    if duration[visit_duration_plan] in list(visit_duration_plan_exists):
        return True
    return False



def check_request_time_feasibility(doctor, request_time,visit_type,visit_duration_plan):
    plan = doctor.plan
    week_day = request_time.date()
    duration = {
        0:15,
        1:30,
        2:45,
    }
    date = False
    visit= VisitType.objects.filter(Doctor_supports=plan,visit_type=visit_type)
    if len(visit) == 0:
        date = False
    work_day_check_exists = WorkDay.objects.filter(visit_type=visit[0].id, date=week_day)
    if work_day_check_exists.exists():
        date = True
    else:
        return False

    if date:
        if WorkTime.objects.filter(Work_day=work_day_check_exists[0]).exists():
            for interval in WorkTime.objects.filter(Work_day=work_day_check_exists[0]):
                time = datetime.strptime('00:00:00', '%H:%M:%S').time()
                if interval.end_time == time:
                    if request_time.time() >= interval.start_time:
                        return True

                if interval.end_time >= (request_time+timedelta(minutes=duration[visit_duration_plan])).time() >= interval.start_time: #check
                    return True
    return False

class VisitPlanCreate(generics.ListCreateAPIView):
    serializer_class = VisitPlanSerializer
    permission_classes = (IsAuthenticated,)
    def perform_create(self, serializer):
        user = self.request.user
        patient = get_object_or_404(Patient,user=user)
        if not serializer.validated_data.get('doctor'): raise PermissionDenied(
            {'detail': "invalid doctor", "error_code": 603})

        doctor = serializer.validated_data['doctor']
        if not check_transaction_possibility_plan(serializer,patient.user, doctor,perform=True):
            raise PermissionDenied({'detail': "اعتبار شما برای این درخواست کافی نمیباشد", "error_code": 602})

        panel, created = Panel.objects.get_or_create(patient=patient, doctor=doctor)
        if created: panel.enabled = False
        plan = serializer.validated_data['plan']
        serializer.save(patient=patient, panel=panel,plan=plan)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doctor = serializer.validated_data['doctor']
        queryset = VisitPlan.objects.filter(patient__user=self.request.user,enabled=True,doctor=doctor)
        if len(queryset) != 0 :
            return Response(status=HTTP_200_OK, data={"success": True, "created": False})
        self.perform_create(serializer)
        return Response(status=HTTP_200_OK, data={"success": True, "created": True})
    def list(self, request, *args, **kwargs):
        self.check_permission()
        partner = self.request.query_params.get('partner')
        if self.request.user.type == 0:
            queryset = VisitPlan.objects.filter(patient__user=self.request.user,enabled=True,doctor=partner)

        else:
            queryset = VisitPlan.objects.filter(doctor__user=self.request.user,enabled=True,patient=partner)

        serializer = VisitPlanSerializer(queryset, many=True)
        return Response(serializer.data)

    def check_permission(self):
        user = self.request.user
        if user.type == 2:
            raise PermissionDenied()


class TerminateChat(generics.UpdateAPIView):
    serializer_class = VisitPlanSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def get_object(self):
        self.check_permission()
        return self.visitplan

    def check_permission(self):
        user = self.request.user
        if user.type != 1:
            raise PermissionDenied()
        visit_plan_id = self.request.data.get('visit_text_plan_id')
        status = self.request.data.get('enabled')
        panel_id = self.kwargs.get('id')
        panel = get_object_or_404(Panel,pk=panel_id)
        patient_id = panel.patient.id
        patient = get_object_or_404(Patient,pk=patient_id)
        if not visit_plan_id:
            visitplan = VisitPlan.objects.filter(panel=panel_id).order_by('-id')
            if status == True:
                if len(visitplan)==0:
                    user = self.request.user
                    doctor = get_object_or_404(Doctor, user=user)
                    clinic = doctor.clinic
                    plan_id = get_object_or_404(ClinicPlan,clinic=clinic)
                    visitplan = VisitPlan.objects.create(doctor=doctor, panel=panel, plan=plan_id,patient=patient)
                else:
                    visitplan = visitplan[0]
            else:raise PermissionDenied()
        else:
            visitplan = get_object_or_404(VisitPlan, pk=visit_plan_id,panel=panel_id)
        self.visitplan = visitplan



class VisitListCreate(generics.ListCreateAPIView):
    serializer_class = VisitSerializer
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthenticated,)
    filter_fields = {'request_visit_time': ['gte', 'lt']}

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VisitSerializerWithUsers(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = VisitSerializerWithUsers(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        status = self.request.query_params.get('status')
        visit_type = self.request.query_params.get('visit_type')
        query = self.request.query_params.get('query')
        user = self.request.user
        return get_relevant_visit_queryset_pending(user, visit_type, query, status)

    def perform_create(self, serializer):

        user = self.request.user
        patient = get_object_or_404(Patient, user=user)
        print(patient.id)
        if not serializer.validated_data.get('doctor'): raise PermissionDenied(
            {'detail': "invalid doctor", "error_code": 603})
        doctor = serializer.validated_data['doctor']
        screening_step_id = self.request.data.get('screening_step_id')
        request_visit_time = serializer.validated_data['request_visit_time']
        visit_type = serializer.validated_data['visit_type']
        type = serializer.validated_data.get('type')
        visit_duration_plan = serializer.validated_data['visit_duration_plan']
        ScreeningSteps.objects.filter(pk=screening_step_id).update(visit_status=True)

        if request_visit_time < timezone.now():  # todo
            raise PermissionDenied({'detail': "امکان رزرو در تاریخ یا زمان گذشته فراهم نمی باشد.", "error_code": 600})

        if not check_interference(doctor, request_visit_time, visit_duration_plan):
            raise PermissionDenied({'detail': "تداخل زمانی با درخواست های ویزیت دیگر", "error_code": 600})

        if not check_request_time_feasibility(doctor, serializer.validated_data.get('request_visit_time'),visit_type,visit_duration_plan):
            raise PermissionDenied(
                {'detail': "لطفا در بازه‌های زمانی ممکن زمان ویزیت را انتخاب کنید", "error_code": 601})

        if not check_plan_feasibility(doctor,visit_type,visit_duration_plan):
            raise PermissionDenied(
                {'detail': "لطفا بازه های درست را انتخاب کنید.", "error_code": 614})
        if request_visit_time <= timezone.now()+timedelta(hours = 6):
            raise PermissionDenied({'detail': "اختلاف تایم درخواست ویزیت و تایم ویزیت باید بیش تر از ۶ ساعت باشد.", "error_code": 626})
        if not screening_step_id and type==0 :
            if not check_transaction_possibility(serializer, patient.user, doctor,visit_type, perform=True):
                raise PermissionDenied({'detail': "اعتبار شما برای این درخواست کافی نمیباشد", "error_code": 602})

        panel, created = Panel.objects.get_or_create(patient=patient, doctor=doctor)

        visit_instance = serializer.save(patient=patient, panel=panel)
        async_auto_reject_visit.apply_async(args=(visit_instance.id,),
                                            eta=timedelta(minutes=2) + visit_instance.request_visit_time)
        async_auto_recall_doctor_to_answer.apply_async(args=(visit_instance.id,),
                                                       eta=visit_instance.request_visit_time - timedelta(minutes=15))
        if created: panel.enabled = False
        type_ = {0: 'معمولی', 1: 'ICA',2: 'بازی های شناختی',3: 'غربالگری'}

        # panel.status = visit_instance.visit_type
        panel.save(update_fields=['status', 'enabled'])
        visit_dict = VisitSerializer(visit_instance).data
        body_info = f'نام بیمار: {patient.user.first_name} {patient.user.last_name}'
        if visit_dict['type'] == 0:
            header_info = 'درخواست ویزیت'
        else:
            header_info = f'درخواست ویزیت : {type_[visit_dict["type"]]}'
        send_async_notification.apply_async(args=(header_info, body_info, doctor.user.id, {"type": 5, "payload": visit_dict}, datetime.now(), 5))
        auto_disable_screening.apply_async(args=(screening_step_id,),
                                       eta=request_visit_time + timedelta(minutes=30))

class VisitRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VisitSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'

    def check_permission(self):
        visit_id = self.kwargs.get('id')
        visit = get_object_or_404(Visit, pk=visit_id)
        user = self.request.user
        if self.request.data.get("status"): self.request.data.pop("status")
        if user.type == 0:
            if self.request.data.get("doctor_message"): self.request.data.pop("doctor_message")
            if visit.patient is not None and visit.patient.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        else:
            if self.request.data.get("patient_message"): self.request.data.pop("patient_message")
            if visit.doctor is not None and visit.doctor.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        self.visit = visit

    def get_queryset(self):
        user = self.request.user
        if user.type == 0:
            return Visit.objects.filter(patient__user=user)
        else:
            return Visit.objects.filter(doctor__user=user)

    def get_object(self):
        self.check_permission()
        return self.visit


class VisitRelatedRetrieve(generics.RetrieveAPIView):
    serializer_class = VisitSerializer
    permission_classes = (IsAuthenticated,)

    def check_permission(self):
        partner_id = self.kwargs.get('id')  # partner may be doctor or patient
        user = self.request.user
        if user.type == 0:
            visit = Visit.objects.filter(doctor=partner_id, patient__user=user).last()
        else:
            visit = Visit.objects.filter(patient=partner_id, doctor__user=user).last()
        if not visit: raise NotFound(detail="u dont have any [visit request] with such partner ", code=404)
        if self.request.data.get("status"): self.request.data.pop("status")
        print(visit.patient.user.username)
        if user.type == 0:
            if self.request.data.get("doctor_message"): self.request.data.pop("doctor_message")
            if visit.patient is not None and visit.patient.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        else:
            if self.request.data.get("patient_message"): self.request.data.pop("patient_message")
            if visit.doctor is not None and visit.doctor.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        return visit

    def get_object(self):
        return self.check_permission()


class VisitRelatedRetrieveAccepted(generics.RetrieveAPIView):
    serializer_class = VisitSerializer
    permission_classes = (IsAuthenticated,)

    def check_permission(self):
        partner_id = self.kwargs.get('id')  # partner may be doctor or patient
        user = self.request.user
        if user.type == 0:
            visit = Visit.objects.filter(doctor=partner_id, patient__user=user, status=1).order_by(
                'created_date').last()
        else:
            visit = Visit.objects.filter(patient=partner_id, doctor__user=user, status=1).order_by(
                'created_date').last()
        if not visit: raise NotFound(detail="u dont have any [visit request] with such partner ", code=404)
        if user.type == 0:
            if visit.patient is not None and visit.patient.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        else:
            if visit.doctor is not None and visit.doctor.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        return visit

    def get_object(self):
        return self.check_permission()


class VisitRelatedRetrieveAcceptedNearest(generics.RetrieveAPIView):
    serializer_class = VisitSerializer
    permission_classes = (IsAuthenticated,)

    def check_permission(self):
        partner_id = self.kwargs.get('id')  # partner may be doctor or patient
        user = self.request.user
        if user.type == 0:
            visit = Visit.objects.filter(doctor=partner_id, patient__user=user, status=1,
                                         request_visit_time__gte=(timezone.now() - timedelta(
                                             minutes=1) * ((1 + F("visit_duration_plan")) * 15))).order_by(
                'request_visit_time').first()
        else:
            visit = Visit.objects.filter(patient=partner_id, doctor__user=user, status=1,
                                         request_visit_time__gte=(timezone.now() - timedelta(
                                             minutes=1) * ((1 + F("visit_duration_plan")) * 15))).order_by(
                'request_visit_time').first()
        if not visit: raise NotFound(detail="u dont have any [visit request] with such partner ", code=404)
        if user.type == 0:
            if visit.patient is not None and visit.patient.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        else:
            if visit.doctor is not None and visit.doctor.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        return visit

    def get_object(self):
        return self.check_permission()


class ResponseVisit(generics.UpdateAPIView):
    serializer_class = VisitSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'

    def check_permission(self):
        visit_id = self.kwargs.get('id')
        visit = get_object_or_404(Visit, pk=visit_id)
        print(visit)
        user = self.request.user
        if user.type == 0:
            raise PermissionDenied({'detail': "patient can response  visit", "error_code": 611})
        else:
            if self.request.data.get("patient_message"): self.request.data.pop("patient_message")
            if self.request.data.get("title"): self.request.data.pop("title")
            if visit.doctor is not None and visit.doctor.user != user:
                raise PermissionDenied({'detail': "not related visit", "error_code": 610})
        self.visit = visit

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        accepted_before = False
        if instance.status == 1:
            accepted_before = True

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # here we check what is doctor response to update panel of the patient
        if instance.status == 1 and not accepted_before:
            full_panel_with_dynamic_fields(instance.panel)
            # instance.panel.status = 2 + instance.visit_type
            instance.panel.enabled = True
            instance.panel.save()
            # charge_doctor(instance, instance.patient.user, instance.doctor,instance.visit_type)
            async_auto_recall_visit.apply_async(args=(instance.id,),
                                                eta=instance.request_visit_time - timedelta(minutes=5))



        elif instance.enabled:
            refund_transaction(instance, accepted_before)
            # instance.panel.status = 7
            instance.enabled = False
            instance.status = 2
            if not instance.panel.enabled:
                if Visit.objects.filter(panel=instance.panel, enabled=True, status=0).count() <= 1:
                    instance.panel.delete()

        instance.save()
        if instance.status == 2:
            request_result = "رد درخواست"
        elif instance.status == 1:
            request_result = "قبول درخواست"
        else:
            request_result = "نتیجه درخواست"
        instance = self.get_object()
        visit_dict = VisitSerializer(instance).data
        body_info = f'نام دکتر: {self.request.user.first_name} {self.request.user.last_name}'
        send_async_notification.apply_async(
            args=(request_result, body_info, instance.patient.user.id, {"type": 6, "payload": visit_dict}, datetime.now(), 6))

        return Response(serializer.data)

    def get_object(self):
        self.check_permission()
        return self.visit


class CreateFile(generics.CreateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser,)

    def perform_create(self, serializer):

        # self.check_permission()

        serializer.save(list_id=self.kwargs['list_id'], user=self.request.user)

    def check_permission(self):
        partner_id = self.request.query_params.get('partner_id')
        if self.request.user.type == 0:
            visit = Visit.objects.filter(status=1, doctor=partner_id, patient__user_id=self.request.user.id)
            if len(visit) == 0:
                raise PermissionDenied({'msg': errors[621], 'code': 621})
        elif self.request.user.type == 1:
            visit = Visit.objects.filter(status=1, doctor__user_id=self.request.user.id, patient=partner_id)
            if len(visit) == 0:
                raise PermissionDenied({'msg': errors[621], 'code': 621})


class UpdateImage(generics.UpdateAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser,)

    def perform_create(self, serializer):
        serializer.save(list_id=self.kwargs['list_id'], )


class DeleteFile(generics.DestroyAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user:
            if obj.user.username == self.request.user.username:
                super().delete(self, request, *args, **kwargs)
                return Response({'success': True})
                # return super().delete(self, request, *args, **kwargs)

        raise PermissionDenied({'detail': 'you can not delete this file', "error_code": 612})

    # def check_permission(self):
    #     user = self.request.user
    #     if user.type == 0 :
    #         raise PermissionDenied({'detail': 'u are not doctor', "error_code": 612})


class UpdateDQAnswer(generics.UpdateAPIView):
    queryset = DQAnswer
    serializer_class = DQAnswerSerializer


class RetrieveDoctor(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = BriefDoctorSerializerWithoutPanels


class RetrieveClinic(generics.RetrieveAPIView):
    queryset = Clinic.objects.all()
    serializer_class = BriefClinicSerializerWithFullServices


class RetrievePatient(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = BriefPatientsSerializer


class RetrieveImageList(generics.RetrieveAPIView):
    queryset = ImageList.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ImageListSerializer


class RetrieveUpdateDoctorSupport(generics.RetrieveUpdateAPIView): #change
    queryset = DoctorSupports
    permission_classes = (IsAuthenticated,)
    serializer_class = DoctorSupportsSerializer

    def get_object(self):
        user = self.request.user
        me = get_object_or_404(Doctor, user=user)
        return me.plan

    def update(self, request, *args, **kwargs):
        visit_types = self.request.data.pop('visit_types', None)
        instance = self.get_object()
        VisitType.objects.filter(Doctor_supports=instance).delete()
        if visit_types:
            for index,visit_type in enumerate(visit_types):
                visit_type_ser = VisitTypeSerializerFull(data=visit_type)
                visit_type_ser.is_valid(raise_exception=True)
                visit_type_ser.save(Doctor_supports=instance)
                visit_type_instance = VisitType.objects.filter(Doctor_supports=instance)[index]
                if "work_days" in visit_type:
                    for work_day in visit_type["work_days"]:
                        work_day_ser = WorkDaySerializer(data=work_day)
                        work_day_ser.is_valid(raise_exception=True)
                        work_day_ser.save(visit_type=visit_type_instance)
                        work_day_instance = WorkDay.objects.filter(visit_type=visit_type_instance, date=work_day['date'])[0]
                        if "work_times" in work_day:
                            for work_time in work_day["work_times"]:
                                work_time_ser = WorkTimeSerializer(data=work_time)
                                work_time_ser.is_valid(raise_exception=True)
                                work_time_ser.save(Work_day=work_day_instance)

        return super().update(request, *args, **kwargs)


class RetrieveDoctorSupport(generics.RetrieveAPIView):
    queryset = DoctorSupports.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = BriefDoctorSupportsSerializerWithReserveVisit

    def get_object(self):
        doctor_id = self.kwargs.get('id')
        doctor = get_object_or_404(Doctor, id=doctor_id)
        return doctor.plan


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agora_channel_name(request):
    user = request.user
    # user_id = request.query_params.get('user_id')
    visit_id = request.query_params.get('visit_id')
    visit = get_object_or_404(Visit, pk=visit_id)
    info = VisitSerializer(visit)
    visit_type = visit.visit_method
    # if request.user.type == 0 :
    # partner_info = BriefUserSerializer(User.objects.filter(id=user.id))
    partner_info = UserSerializer(user)

    # elif request.user.type == 1 :
    #     partner_info  = get_object_or_404(Doctor, id=doctor_id)

    channel_name = "AG_p" + str(visit.patient.id) + "_d" + str(visit.doctor.id)
    METHOD_TYPES = {0: 'متنی', 1: 'صوتی', 2: 'تصویری'}
    convert_to_text = METHOD_TYPES[visit_type]
    title = f' تماس {convert_to_text}'
    if user.type == 0:
        send_message_to = visit.doctor.user.id
        body_info = f' نام بیمار :{user.first_name} {user.last_name}'

    else:
        send_message_to = visit.patient.user.id
        body_info = f' نام دکتر :{user.first_name} {user.last_name}'

    send_async_notification.apply_async(args=(title, body_info, send_message_to, {"type": 1, "payload": {"channel_name": channel_name, "partner_info": partner_info.data, "visit": info.data}}, datetime.now(), 1))
    return Response({"channel_name": channel_name})


class NotificationListUpdate(generics.UpdateAPIView, generics.ListAPIView):
    """ this func is for getting notification"""
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        notifications_list = Notification.objects.filter(owner=user.id, enabled=True)
        # notifications_list.filter(Q(data__type=3)| Q(data__type=2)|(~Q(data__type__in=[2,3,1]) & Q(data__payload__request_visit_time__gte=(timezone.now() - timedelta(minutes=1) * ((1 + F("visit_duration_plan")) * 15))))
        #                           |(~Q(data__type=1) & Q(data__payload__visit__request_visit_time__gte=(timezone.now() - timedelta(minutes=1) * ((1 + F("visit_duration_plan")) * 15))))).order_by('-time')
        notifications_list=notifications_list.filter(Q(data__type=3)| Q(data__type=2)| Q(data__type=9)|Q(data__type=10)|(~Q(data__type__in=[2,3,1]) & Q(data__payload__request_visit_time__gte=(timezone.now()).isoformat()))
                                  |(~Q(data__type=1) & Q(data__payload__visit__request_visit_time__gte=(timezone.now()).isoformat()))).order_by('is_read','-time')

        # print(222,a)
        return notifications_list

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_read = True
        instance.save()
        return Response({'success': True})

    def get_object(self):
        notif_id = self.request.query_params.get('notif_id')
        return get_object_or_404(Notification, id=notif_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_tracking(request):
    """ this func is for getting main page of doctors"""
    user = request.user
    panels = search_my_relevant_patient_panels(user)
    # compute statistics
    visit_pending = panels.filter(status__in=[0, 1])
    physical_accepted_count = panels.filter(status=2).count()
    physical_curing_count = panels.filter(status=4).count()
    virtual_accepted_count = panels.filter(status=3).count()
    virtual_curing_count = panels.filter(status=5).count()

    response_data = {"all": panels.count(), 'visit_pending': visit_pending.count(),
                     'virtual_accepted': virtual_accepted_count + virtual_curing_count,
                     'physical_accepted': physical_accepted_count + physical_curing_count}
    recent_panel = panels.first()
    # add recent chats
    if recent_panel:
        print(recent_panel.patient)
        response_data['patient'] = BriefPatientsSerializerJustIdAndNameAndAvatar(recent_panel.patient).data
        response_data['recent_chats'] = MessageSerializer(
            ChatMessage.objects.filter(panel=recent_panel, direction=0).order_by("-modified_date")[:2], many=True).data

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_patient_detailed(request, *args, **kwargs):
    """ get all patient detailed associated with requesting doctor"""
    user = request.user
    patient_id = kwargs['id']
    if not patient_id: raise PermissionDenied({'detail': "mention the patient", "error_code": 609})
    panel = get_my_partner_panel(user, patient_id)
    patient = panel.patient
    panel_serializer = PanelSerializerWithoutDoctor(panel)
    drugs = Drug.objects.filter(doctor__user=user, patient=patient).order_by('-consuming_day')
    drug_serializer = DrugSerializerWithoutPatientAndDoctor(drugs, many=True)
    doctor_events = get_relevant_health_events_queryset(user)
    doctor_patient_events = doctor_events.filter(
        Q(owner=patient.user) | Q(invited_patients=patient)).order_by('-time')
    events_serializer = HealthEventSerializerJustIdAndNameForParticipates(doctor_patient_events, many=True)
    return Response({"panel": panel_serializer.data, 'drugs': drug_serializer.data, 'events': events_serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def on_call_visit(request, *args, **kwargs):
    """ here we use rand int to assign an online random doctor to a patient"""
    user = request.user
    serializer = VisitSerializer(data={"title": "ویزیت رایگان مجازی", 'status': 0})
    serializer.is_valid(raise_exception=True)
    patient = get_object_or_404(Patient, user=user)
    query = Doctor.objects.filter(user__online__gt=0)
    counts = query.count()
    if counts == 0:
        Response({"detail": "در حال حاضر دکتر پاسخگویی وجود ندارد"})
    doctor = query[randint(0, counts - 1)]
    panel, created = Panel.objects.get_or_create(patient=patient, doctor=doctor)
    visit_instance = serializer.save(patient=patient, panel=panel, doctor=doctor)
    if created: panel.enabled = False
    # panel.status = 0
    visit_dict = VisitSerializer(visit_instance).data
    panel.save(update_fields=["enabled", ])
    ChatConsumer.send_panel_notification(visit_dict, "VISIT_REQUEST", panel.id)
    body_info = f' نام بیمار:{patient.user.first_name} {patient.user.last_name}'
    send_async_notification.apply_async(
        args=("درخواست ویزیت رایگان", body_info, doctor.user.id, {"type": 4, "payload": visit_dict}, datetime.now(), 4))
    return Response(serializer.data)


class LogoBankListCreate(generics.ListAPIView):
    serializer_class = BankLogoSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        code = self.request.query_params.get('code')
        banks = BankLogo.objects.all().filter(enabled=True)

        if code:
            banks = banks.filter(number__icontains=code)

        return banks
