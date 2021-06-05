# Create your views here.
from datetime import datetime
from django.contrib.auth import authenticate, get_user_model
from kavenegar import *
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework_jwt.views import obtain_jwt_token, ObtainJSONWebToken, jwt_response_payload_handler
from rest_framework.exceptions import NotFound, PermissionDenied
from authentication.models import User, Patient, Doctor, Clinic, DoctorSupports, SuggestedDoctor
from authentication.permissions import IsAdminOrOwner
from authentication.serializers import UserSerializer, SuggestedDoctorSerializer, ProfileImageSerializer
from authentication.tasks import send_verification_code
from follow_up.serializers import DoctorSerializer, PatientSerializer, ClinicSerializer
from utils.models import ImageList
from utils.utils import generate_digit_code
import re
from utils.errors import errors
from follow_up.tasks import send_async_notification
from follow_up.models import Panel
from django.contrib.auth.models import update_last_login

def update_user(request, user): # update info of user
    if request.data.get('user'):
        us = UserSerializer(user, data=request.data.get('user'), partial=True)
        us.is_valid(raise_exception=True)
        us.save()
    return request


@api_view(['POST'])
def log_in(request):
    """

    :param request:
         user_name : str
            username is mobile number
         user_type : int
            user_type is 0 or 1 or 2
    :return:
        dict
        a list of strings used that are the header columns
    """
    payload = json.loads(request.body)
    phone = payload.get('username', None)
    user_type = payload.get('user_type', None)
    if phone is None:
        raise PermissionDenied({'msg': errors[100], 'code': 100})
    if user_type is None:
        raise PermissionDenied({'msg': errors[101], 'code': 101})
    rule = re.compile(r'^(?:\+?)?[0]\d{10}$')  # validate mobile number
    validate_phone = rule.search(phone)

    if validate_phone == None:
        raise PermissionDenied({'msg': errors[102], 'code': 102})
    if not isinstance(user_type, int):  # if user_type is not integre error
        raise PermissionDenied({'msg': errors[103], 'code': 103})
    if user_type not in [0, 1, 2]:  # 0 is patient -1 is doctor - 2 is clinic
        raise PermissionDenied({'msg': errors[104], 'code': 104})
    user = User.objects.filter(username=phone)
    user_type = int(user_type)
    created = True
    if len(user) is 0:  # if user there is not in database
        if user_type == 1:
            # doctor_plan = DoctorSupports.objects.create()
            # Doctor(user=user, plan=doctor_plan).save()
            raise PermissionDenied({'msg': errors[105], 'code': 105})  # no person can not create doctor account in application
        user = User(username=phone, phone_number=phone, type=user_type)
        user.verified = False
        user.save()
        if user_type == 0:
            documents = ImageList.objects.create(title='documents')
            Patient(user=user, documents=documents).save()

        else:
            Clinic(user=user).save()
    else:  # if user there is in database we can not create ..and in out put we put create equal to false
        user = user[0]  # if user there is in database--->because output of filter is list ..and username in database is not duplicate,we get zero index
        user_type_in_db = user.type
        if user_type_in_db != user_type:  # if person want to login for second time and select other types...she or he must receive the error, because she or he cannot be both a patient and a doctor with one number
            raise PermissionDenied({'msg': errors[615], 'code': 615})
        if user.verified:
            created = False
    verify_code = generate_digit_code(6)  # create random number
    # verify_code = 123456
    user.set_password(verify_code)  # use random number as password and use set_password for creating hash password
    user.save()
    send_verification_code.delay(phone, verify_code)  # send sms verify_code with celery task
    return Response(status=HTTP_200_OK, data={"success": True, "created": created})


class Verification(ObtainJSONWebToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            user = get_user_model().objects.get(username=request.data[get_user_model().USERNAME_FIELD])
            user.verified = True
            update_last_login(None, user)
            user.save()
            first_name = user.first_name
            last_name = user.last_name
            national_id = user.national_id
            if first_name == None:
                first_name = ''
            if last_name == None:
                last_name = ''
            if national_id == None:
                national_id = ''
            if user.type == 1:
                response.data['expert'] = user.udoctor.all()[0].expert
            response.data['firstname'] = first_name
            response.data['lastname'] = last_name
            response.data['nationalcode'] = national_id
        return response


class DoctorProfile(generics.RetrieveUpdateDestroyAPIView):
    """
        every doctor can update and see his/her profile with permission_classes access
    """
    serializer_class = DoctorSerializer
    permission_classes = (IsAdminOrOwner, IsAuthenticated)  # for accessing this method you must login

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clinic_id = None

    def get_object(self):
        user = self.request.user
        return get_object_or_404(Doctor, user=user)

    def update(self, request, *args, **kwargs):  # TODO ask about this method
        request = update_user(request, self.request.user)
        if request.data.get('clinic_id'):  # doctor can not change her/his clinic_id
            request.data.pop('clinic_id')
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):  # TODO ask about this method
        if self.clinic_id:
            clinic = get_object_or_404(Clinic, pk=self.clinic_id)
            serializer.save(clinic=clinic)
            return
        serializer.save()


class PatientProfile(generics.RetrieveUpdateDestroyAPIView):
    """
        in this class patient can update his/her profile fields (only fields that define in PatientSerializer) or patient can see info of own profile
    """
    serializer_class = PatientSerializer
    permission_classes = (IsAdminOrOwner, IsAuthenticated)

    def get_object(self):  # get info of patient
        user = self.request.user
        return get_object_or_404(Patient, user=user)

    def update(self, request, *args, **kwargs):  # update info of user patient (fields that in serializer)
        # print(111,self.request.data.get("height"))
        if self.request.data.get("clinic"):
            clinic = get_object_or_404(Clinic, pk=self.request.data.get("clinic"))
            doctor_user = clinic.user
            patient = self.get_object()
            patient_info = PatientSerializer(patient).data
            doctor = get_object_or_404(Doctor, user=doctor_user)
            panel, created = Panel.objects.get_or_create(patient=patient, doctor=doctor)

        request = update_user(request, self.request.user)
        if self.request.data.get("clinic"):
            body_info = f'نام بیمار: {request.user.first_name} {request.user.last_name}'
            send_async_notification.apply_async(args=("ثبت نام بیمار جدید", body_info, doctor.user.id, {"type": 9, "payload": patient_info}, datetime.now(), 9))
        return super().update(request, *args, **kwargs)


class ClinicProfile(generics.RetrieveUpdateDestroyAPIView):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = (IsAdminOrOwner, IsAuthenticated)

    def get_object(self):
        user = self.request.user
        return get_object_or_404(self.queryset, user=user)

    def update(self, request, *args, **kwargs):
        request = update_user(request, self.request.user)
        return super().update(request, *args, **kwargs)


class SuggestedDoctorCreate(generics.CreateAPIView):  # only the patient can suggest doctor
    queryset = SuggestedDoctor.objects.all()
    serializer_class = SuggestedDoctorSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        self.check_permission()
        serializer.save()

    def check_permission(self):
        user = self.request.user
        if not user.type == 0:
            raise PermissionDenied({'msg': errors[604], 'code': 604})


class UploadProfileImage(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileImageSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return User.objects.get(username=self.request.user)

    def update(self, request, *args, **kwargs):
        self.check_permission()
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        self.check_permission()
        instance = self.get_object()
        if instance.avatar == "":
            return Response({'error': "There is not image"})
        instance.avatar.delete()
        return Response({'success': True})

    def check_permission(self):
        user = self.request.user
        if user.type == 0:
            if user.upatient.all()[0].id != self.kwargs.get('pk'):
                raise PermissionDenied()
        elif user.type == 1:
            if user.udoctor.all()[0].id != self.kwargs.get('pk'):
                raise PermissionDenied()
        elif user.type == 2:
            if user.uclinic.all()[0].id != self.kwargs.get('pk'):
                raise PermissionDenied()
