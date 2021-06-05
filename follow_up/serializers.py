from rest_framework import fields, serializers
from authentication.models import Clinic, ClinicPlan, Patient, Doctor, DoctorSupports, WorkTime, WorkDay, VisitType
from authentication.serializers import BriefUserSerializer, UserSerializer, BriefBriefUserSerializer, \
    BriefBriefUserSerializerWithAvatar
from follow_up.models import Panel, DiseaseQuestion, DQAnswer, Ticket, Visit, ClinicService, HealthEvent, Drug, Article, \
    BankLogo, Notification, VisitPlan, Screening, ScreeningSteps,Ica
from follow_up.utils import update_panel_status, change_panel_representation, change_drug_representation
from utils.costumed_field import Base64ImageField
from utils.serializers import ImageListSerializer, ImageListSerializerJustIdAndTitle
from django.utils import timezone
from datetime import timedelta
from django.db.models import F
from medical_test.serializers import CognitiveTestSerializerWithoutQA


class ScreeningSerializer(serializers.ModelSerializer):
    # medical_tests = serializers.StringRelatedField(many=True)
    class Meta:
        model = Screening
        fields = ('id', 'clinic', 'price', 'medical_tests')
        read_only_fields = ['id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['medical_tests'] = []
        for entry in instance.medical_tests.all():
            medical_tests = CognitiveTestSerializerWithoutQA(entry).data
            representation['medical_tests'].append(medical_tests)
        return representation


class ScreeningStepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreeningSteps
        fields = '__all__'
        read_only_fields = ['id']

class IcaSerializer(serializers.ModelSerializer):
    class Meta:
        model= Ica
        fields = '__all__'
        read_only_fields = ['id']


class WorkTimeSerializerJustStartEnd(serializers.ModelSerializer):
    class Meta:
        model = WorkTime
        exclude = ('id', 'Work_day', 'created_date', 'modified_date', 'enabled')
        read_only_fields = ['id']


class WorkTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkTime
        fields = "__all__"


class WorkDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkDay
        fields = "__all__"


class WorkDaySerializerFull(serializers.ModelSerializer):
    work_times = WorkTimeSerializerJustStartEnd(many=True)

    class Meta:
        model = WorkDay
        exclude = ('id', 'visit_type', 'created_date', 'modified_date', 'enabled')
        read_only_fields = ['id']


class VisitTypeSerializerFull(serializers.ModelSerializer):  # change

    TYPES = ((0, 'حضوری'), (1, 'مجازی'))
    visit_type = fields.ChoiceField(choices=TYPES)
    METHOD_TYPES = ((0, 'متنی'), (1, 'صوتی'), (2, 'تصویری'))
    visit_method = fields.MultipleChoiceField(choices=METHOD_TYPES)
    PLANS = ((0, '1۵ دقیقه'), (1, '۳۰ دقیقه'), (2, '۴۵ دقیقه'))
    visit_duration_plan = fields.MultipleChoiceField(choices=PLANS, )
    work_days = WorkDaySerializerFull(many=True, read_only=True)

    class Meta:
        model = VisitType
        fields = "__all__"
        read_only_fields = ['id']


class VisitTypeSerializer(serializers.ModelSerializer):
    TYPES = ((0, 'حضوری'), (1, 'مجازی'))
    visit_type = fields.ChoiceField(choices=TYPES)
    METHOD_TYPES = ((0, 'متنی'), (1, 'صوتی'), (2, 'تصویری'))
    visit_method = fields.MultipleChoiceField(choices=METHOD_TYPES)
    PLANS = ((0, '1۵ دقیقه'), (1, '۳۰ دقیقه'), (2, '۴۵ دقیقه'))
    visit_duration_plan = fields.MultipleChoiceField(choices=PLANS, )
    work_days = WorkDaySerializerFull(many=True, read_only=True)

    class Meta:
        model = VisitType
        exclude = ('id', 'Doctor_supports', 'created_date', 'modified_date', 'enabled')
        read_only_fields = ['id']


class DoctorSupportsSerializer(serializers.ModelSerializer):
    visit_types = VisitTypeSerializer(many=True)

    class Meta:
        model = DoctorSupports
        fields = "__all__"
        read_only_fields = ['id']


class BriefDoctorSupportsSerializer(serializers.ModelSerializer):
    visit_types = VisitTypeSerializer(many=True)

    class Meta:
        model = DoctorSupports
        exclude = ['modified_date', 'created_date', "id", "enabled"]
        read_only_fields = ['id']


class BriefDoctorSupportsSerializerWithReserveVisit(serializers.ModelSerializer):  # change
    visit_types = VisitTypeSerializer(many=True)
    recent_visits = serializers.SerializerMethodField('get_visits')

    class Meta:
        model = DoctorSupports
        fields = ['visit_types', 'recent_visits']

    def get_visits(self, obj):
        visits = Visit.objects.filter(doctor=self.context['view'].kwargs['id'], status__in=[0, 1],
                                      request_visit_time__gte=(timezone.now() - timedelta(
                                          minutes=1) * ((1 + F("visit_duration_plan")) * 15))).order_by(
            'request_visit_time')
        visits_list = VisitSerializerJustIdAndStatusAndDate(visits, many=True)
        return visits_list.data


class DiseaseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseQuestion
        exclude = ['modified', 'created']


class DQAnswerSerializer(serializers.ModelSerializer):
    question = serializers.StringRelatedField()

    class Meta:
        model = DQAnswer
        fields = ['id', 'question', 'answer']


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['modified', 'created']


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = '__all__'
        read_only_fields = ['modified', 'created']


class VisitSerializerJustIdAndTitle(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ('id', 'title')


class VisitSerializerJustIdAndStatusAndDate(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ('id', 'visit_type', 'status', 'visit_duration_plan', 'request_visit_time')


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = '__all__'
        read_only_fields = ['modified', 'created']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_drug_representation(instance, representation)


class DrugSerializerWithoutPatientAndDoctor(serializers.ModelSerializer):
    class Meta:
        model = Drug
        exclude = ['patient', 'doctor']
        read_only_fields = ['modified', 'created']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_drug_representation(instance, representation)


class ProfileReadyPanelSerializer(serializers.ModelSerializer):  # panel serializer for retrieving profile
    panel_image_sets = ImageListSerializerJustIdAndTitle(many=True, required=False)
    visits = VisitSerializer(read_only=True, many=True)

    class Meta:
        model = Panel
        fields = ['id', 'status', 'patient', 'doctor', 'modified_date', 'created_date', 'panel_image_sets', 'visits',
                  'enabled']
        read_only_fields = ['modified_date', 'created_date', 'enabled']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_panel_representation(instance, representation)


class VisitPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitPlan
        fields = "__all__"
        read_only_fields = ['id']


class ClinicPlanSerializerFull(serializers.ModelSerializer):
    class Meta:
        model = ClinicPlan
        fields = "__all__"
        read_only_fields = ['id']


class ClinicPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicPlan
        exclude = ('clinic', 'created_date', 'modified_date', 'enabled')
        read_only_fields = ['id']


class ClinicSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True, required=False)
    pclinic = ClinicPlanSerializer(many=True)

    class Meta:
        model = Clinic
        fields = ['id', 'user', 'sub_type', 'clinic_name', 'clinic_address', 'description', 'longitude', 'latitude', 'pclinic']
        read_only_fields = ('id',)
class ClinicSerializerwithIdAndAddress(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ['id','clinic_address']
        read_only_fields = ('id',)

class BriefClinicSerializer(serializers.ModelSerializer):
    user = BriefUserSerializer(read_only=True, required=False)
    pclinic = ClinicPlanSerializer(many=True)

    class Meta:
        model = Clinic
        fields = ['id', 'user', 'sub_type', 'clinic_name', 'clinic_address', 'description', 'longitude', 'latitude', 'pclinic']
        read_only_fields = ('id',)


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    panels = ProfileReadyPanelSerializer(many=True)
    clinic = BriefClinicSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'council_code', 'account_number', 'expert', 'clinic', 'panels', 'rate']
        read_only_fields = ('id', 'rate')


# this serializer used to serialize doctor for general users, not admins and doctor himself
class BriefDoctorSerializerWithoutPanels(serializers.ModelSerializer):
    user = BriefUserSerializer(read_only=True)
    clinic = BriefClinicSerializer(read_only=True)
    plan = BriefDoctorSupportsSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'council_code', 'expert', 'clinic', 'plan', 'fee', 'rate']
        read_only_fields = ('id', 'rate')


# this serializer used to serialize doctor for general users, not admins and doctor himself
class BriefDoctorSerializerWithoutClinicAndPanels(serializers.ModelSerializer):
    user = BriefUserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'council_code', 'expert', 'clinic', 'fee', 'rate']
        read_only_fields = ('id', 'rate')


class BriefDoctorSerializerJustIdAndName(serializers.ModelSerializer):
    user = BriefBriefUserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'rate']
        read_only_fields = ('id', 'rate')


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    documents = ImageListSerializer(read_only=True)
    panels = ProfileReadyPanelSerializer(many=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'documents', 'height', 'weight', 'gender', 'birth_location', 'city','date_of_birth', 'panels','clinic']
        read_only_fields = ('id',)


class BriefPatientsSerializer(serializers.ModelSerializer):
    user = BriefUserSerializer(read_only=True)
    documents = ImageListSerializerJustIdAndTitle(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'documents', ]


class BriefPatientsSerializerWithoutDocuments(serializers.ModelSerializer):
    user = BriefUserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', ]


class BriefPatientsSerializerJustIdNameAvatar(serializers.ModelSerializer):
    user = BriefBriefUserSerializerWithAvatar(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user']
        read_only_fields = ('id',)


class BriefPatientsSerializerJustIdAndNameAndAvatar(serializers.ModelSerializer):
    user = BriefBriefUserSerializerWithAvatar(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user']
        read_only_fields = ('id',)


class ClinicServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicService
        exclude = ['clinic', ]


class BriefClinicSerializerWithFullServices(serializers.ModelSerializer):
    user = BriefUserSerializer(read_only=True, required=False)
    doctors = BriefDoctorSerializerWithoutClinicAndPanels(read_only=True, many=True)
    services = ClinicServiceSerializer(read_only=True, many=True)

    class Meta:
        model = Clinic
        fields = ['id', 'user', 'sub_type', 'clinic_name', 'clinic_address', 'description', 'doctors', 'services',
                  'longitude', 'latitude']
        read_only_fields = ('id',)


class PanelSerializer(serializers.ModelSerializer):
    doctor_info = BriefDoctorSerializerWithoutPanels(source='doctor', required=False)
    patient_info = BriefPatientsSerializer(source='patient', required=False)
    visits = VisitSerializer(read_only=True, many=True)
    panel_image_sets = ImageListSerializer(many=True, required=False)

    class Meta:
        model = Panel
        fields = ['id', 'status', 'doctor', 'patient', 'modified_date', 'created_date', "doctor_info", "patient_info",
                  "panel_image_sets",
                  "visits", 'enabled']
        read_only_fields = ['modified_date', 'created_date', 'enabled']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_panel_representation(instance, representation)


class PanelSerializerJustIdAndTitleOfSubTypes(serializers.ModelSerializer):
    doctor_info = BriefDoctorSerializerWithoutPanels(source='doctor', required=False)
    patient_info = BriefPatientsSerializer(source='patient', required=False)
    visits = VisitSerializer(read_only=True, many=True)
    panel_image_sets = ImageListSerializerJustIdAndTitle(many=True, required=False)

    class Meta:
        model = Panel
        fields = ['id', 'status', 'doctor', 'patient', 'modified_date', 'created_date', "doctor_info", "patient_info",
                  "panel_image_sets",
                  "visits", 'enabled']
        read_only_fields = ['modified_date', 'created_date', 'enabled']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_panel_representation(instance, representation)


class PanelSerializerWithoutDoctor(serializers.ModelSerializer):
    patient_info = BriefPatientsSerializer(source='patient', required=False)
    visits = VisitSerializer(read_only=True, many=True)
    panel_image_sets = ImageListSerializerJustIdAndTitle(many=True, required=False)

    class Meta:
        model = Panel
        fields = ['id', 'status', 'patient', 'modified_date', 'created_date', "patient_info", "visits",
                  'panel_image_sets', 'enabled']
        read_only_fields = ['modified_date', 'created_date', 'enabled']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        update_panel_status(instance)

        old = representation['panel_image_sets']
        representation['panel_image_sets'] = {image_list["title"]: image_list["files"] for image_list in old}
        representation['panel_image_list_name_id'] = {image_list["title"]: image_list["id"] for image_list in old}
        return representation


class PanelSerializerJustPatientIdNameStatus(serializers.ModelSerializer):
    user = BriefPatientsSerializerJustIdNameAvatar(source='patient', required=False, read_only=True)
    id = serializers.PrimaryKeyRelatedField(source='patient', read_only=True)
    visits = VisitSerializerJustIdAndStatusAndDate(many=True, read_only=True)

    class Meta:
        model = Panel
        fields = ['id', 'status', 'user', 'enabled', 'visits']
        read_only_fields = ['modified_date', 'created_date', 'enabled']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        update_panel_status(instance)

        representation['status'] = instance.status
        return representation


class PanelSerializerWithoutPatient(serializers.ModelSerializer):
    doctor_info = BriefDoctorSerializerWithoutPanels(source='doctor', required=False)
    visits = VisitSerializer(read_only=True, many=True)
    panel_image_sets = ImageListSerializerJustIdAndTitle(many=True, required=False)

    class Meta:
        model = Panel
        fields = ['id', 'status', 'doctor', 'modified_date', 'created_date', "visits", "panel_image_sets", 'enabled']
        read_only_fields = ['modified_date', 'created_date', 'enabled']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_panel_representation(instance, representation)


class HealthEventSerializerWithInvitedIDs(serializers.ModelSerializer):
    owner = BriefUserSerializer(read_only=True)
    invited_patients = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all(), required=False, many=True)
    invited_doctors = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), required=False, many=True)

    class Meta:
        model = HealthEvent
        fields = '__all__'
        read_only_fields = ['modified_date', 'created_date']


class HealthEventSerializerWithoutIds(serializers.ModelSerializer):
    owner = BriefUserSerializer(read_only=True)
    invited_patients = BriefPatientsSerializer(required=False, many=True, read_only=True)
    invited_doctors = BriefDoctorSerializerWithoutPanels(required=False, many=True, read_only=True)

    class Meta:
        model = HealthEvent
        fields = '__all__'
        read_only_fields = ['modified_date', 'created_date']


# class EventIntegratedSerializer(serializers.Serializer):
#     visits=VisitSerializer(required=False,many=True)
#     health_events=HealthEventSerializerWithoutIds(required=False,many=True)

class HealthEventSerializerWithoutPatientsDocs(serializers.ModelSerializer):
    owner = BriefUserSerializer(read_only=True)
    invited_patients = BriefPatientsSerializerWithoutDocuments(required=False, many=True, read_only=True)
    invited_doctors = BriefDoctorSerializerWithoutPanels(required=False, many=True, read_only=True)

    class Meta:
        model = HealthEvent
        fields = '__all__'
        read_only_fields = ['modified_date', 'created_date']


class HealthEventSerializerJustIdAndNameForParticipates(serializers.ModelSerializer):
    owner = BriefBriefUserSerializer(read_only=True)
    invited_patients = BriefPatientsSerializerJustIdNameAvatar(required=False, many=True, read_only=True)
    invited_doctors = BriefDoctorSerializerJustIdAndName(required=False, many=True, read_only=True)

    class Meta:
        model = HealthEvent
        fields = ['id', 'owner', 'invited_patients', 'invited_doctors', 'title', 'description', 'time', 'end_time']
        read_only_fields = ['modified_date', 'created_date']


class BriefDrugSerializer(serializers.ModelSerializer):
    patient = BriefPatientsSerializerJustIdNameAvatar(required=False, read_only=True)
    doctor = BriefDoctorSerializerJustIdAndName(required=False, read_only=True)

    class Meta:
        model = Drug
        fields = ['id', 'patient', 'doctor', 'drug_name', 'consuming_time']
        read_only_fields = ['id']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return change_drug_representation(instance, representation)


class ArticleSerializer(serializers.ModelSerializer):
    article_picture = Base64ImageField(max_length=None, use_url=True, )

    class Meta:
        model = Article
        fields = "__all__"


class VisitSerializerWithUsers(serializers.ModelSerializer):
    doctor = BriefDoctorSerializerWithoutClinicAndPanels(read_only=True)
    patient = BriefPatientsSerializerWithoutDocuments(read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'
        read_only_fields = ['modified', 'created']


class BankLogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankLogo
        fields = '__all__'
        read_only_fields = ['number', 'logo']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
