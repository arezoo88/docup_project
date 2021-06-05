from django.db import models
from django.db.models import ForeignKey
from django.utils.text import slugify
from django.utils.timezone import now
from tagging.fields import TagField
from authentication.models import Doctor, Patient, User, Clinic, ClinicPlan
from medical_test.models import CognitiveTest
from utils.models import BaseModel, ImageList, Image,Voucher
import utils.utils as utils
from django.contrib.postgres.fields import JSONField


class Screening(BaseModel):
    price = models.PositiveIntegerField(default=0)
    medical_tests = models.ManyToManyField(to=CognitiveTest, related_query_name='screening',
                                           related_name='screening')
    clinic = models.ForeignKey(to=Clinic, null=True, related_name='Sclinic', blank=True, on_delete=models.CASCADE)


class ScreeningSteps(BaseModel):
    panel = models.ForeignKey(to='Panel', related_name='screeningpanel', on_delete=models.SET_NULL, null=True,blank=True)
    patient = models.ForeignKey(to=Patient, null=True,blank=True, on_delete=models.SET_NULL)
    screening = models.ForeignKey(to=Screening, on_delete=models.SET_NULL, null=True)
    payment_status = models.BooleanField(default=False)
    tests_response_status = JSONField(null=True,blank=True)
    ica_status = models.BooleanField(default=False)
    visit_status = models.BooleanField(default=False)
    STATUS = ((0, 'credit'), (1, 'bank'))
    payment_type = models.IntegerField(choices=STATUS, default=1)
    discount = models.ForeignKey(to=Voucher,on_delete=models.SET_NULL,null=True,blank=True)

class Ica(models.Model):
    screening_step = models.ForeignKey(to=ScreeningSteps,on_delete=models.CASCADE,null=False,blank=False,related_name='sica')
    ica_index = models.IntegerField(null=True,blank=True)
    accuracy = models.IntegerField(null=True,blank=True)
    speed = models.IntegerField(null=True,blank=True)
    accuracy_maintenance = models.IntegerField(null=True,blank=True)
    speed_maintenance = models.IntegerField(null=True,blank=True)
    attention = models.IntegerField(null=True,blank=True)


class Panel(BaseModel):
    doctor = models.ForeignKey(to=Doctor, related_name='panels', on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(to=Patient, related_name='panels', on_delete=models.SET_NULL, null=True)
    panel_image_sets = models.ManyToManyField(to=ImageList, related_query_name='panels',
                                              related_name='panels', )
    STATUS = (
        (0, 'درخواست ویزیت حضوری'), (1, 'درخواست ویزیت مجازی'), (2, 'وریفای حضوری'), (3, 'وریفای مجازی'),
        (4, 'در حال درمان حضوری'), (5, 'در حال درمان مجازی'), (6, 'درمان شده'), (7, 'رد شده'),
    )
    status = models.IntegerField(choices=STATUS, default=0)
    cognitive_tests = models.ManyToManyField(CognitiveTest, through='Panel2CognitiveTest')


class Panel2CognitiveTest(models.Model):
    CognitiveTest = models.ForeignKey(CognitiveTest, on_delete=models.CASCADE)
    panel = models.ForeignKey(to=Panel, on_delete=models.CASCADE, )
    done = models.BooleanField(default=False)
    time_add_test = models.DateTimeField(default=now)


class Ticket(BaseModel):
    doctor = models.ForeignKey(to=Doctor, related_name='tickets', on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(to=Patient, related_name='tickets', on_delete=models.SET_NULL, null=True)
    panel = models.ForeignKey(to=Panel, on_delete=models.CASCADE, null=True, blank=True)
    doctor_message = models.CharField(max_length=512, null=True, blank=True)
    title = models.CharField(max_length=300, null=True, blank=False)
    patient_message = models.CharField(max_length=512, null=True, blank=True)
    STATUS = ((0, 'PENDING'), (1, 'ACCEPT'), (2, 'REJECT'))
    status = models.IntegerField(choices=STATUS, default=0)


class VisitPlan(BaseModel):
    doctor = models.ForeignKey(to=Doctor, related_name='visitdoctorplan', on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(to=Patient, related_name='visitpatientplan', on_delete=models.SET_NULL, null=True)
    panel = models.ForeignKey(to=Panel, related_name='visitpanel', on_delete=models.SET_NULL, null=True)
    plan = models.ForeignKey(to=ClinicPlan, related_name='clinicplans', on_delete=models.SET_NULL, null=True)
    request_visit_plan_time = models.DateTimeField(default=now)

    # active_plan = models.BooleanField(default=True)

    # @property
    # def remaind_message_plan(self):
    #     return self.plan.word_counts


class Visit(BaseModel):
    doctor = models.ForeignKey(to=Doctor, related_name='visits', on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(to=Patient, related_name='visits', on_delete=models.SET_NULL, null=True)
    panel = models.ForeignKey(to=Panel, related_name='visits', on_delete=models.SET_NULL, null=True)
    doctor_message = models.CharField(max_length=512, null=True, blank=True)
    title = models.CharField(max_length=300, null=True, blank=False)
    TYPES = ((0, 'حضوری'), (1, 'مجازی'))
    visit_type = models.IntegerField(choices=TYPES, null=True, blank=True)
    METHOD_TYPES = ((0, 'متنی'), (1, 'صوتی'), (2, 'تصویری'))
    visit_method = models.IntegerField(choices=METHOD_TYPES, null=True, blank=True)
    PLANS = ((0, '1۵ دقیقه'), (1, '۳۰ دقیقه'), (2, '۴۵ دقیقه'))
    visit_duration_plan = models.IntegerField(choices=PLANS, null=True, blank=True)
    patient_message = models.CharField(max_length=512, null=True, blank=True)
    request_visit_time = models.DateTimeField(default=now)
    STATUS = ((0, 'PENDING'), (1, 'ACCEPT'), (2, 'REJECT'))
    status = models.IntegerField(choices=STATUS, default=0)
    type_ = ((0, 'معمولی'),(1, 'ICA'), (2, 'بازی های شناختی'),(3,'غربالگری'))
    type = models.IntegerField(choices=type_, default=0,blank=True)


class ClinicService(BaseModel):
    clinic = models.ForeignKey(to=Clinic, null=True, related_name='services', on_delete=models.CASCADE)
    title = models.CharField(max_length=256, null=True, blank=True)
    service_description = models.TextField(null=True)


# class DiseaseTest(BaseModel):
#     title = models.CharField(max_length=256, null=False, blank=False)
#     test_description = models.TextField(null=True)

############################################################################## previously used models begin
class DiseaseQuestion(BaseModel):
    text = models.CharField(max_length=256, null=False, blank=False)
    multi_choice = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class DQChoice(BaseModel):
    question = models.ForeignKey(to=DiseaseQuestion, on_delete=models.CASCADE, null=False, blank=False,
                                 related_name='choices')
    text = models.CharField(max_length=64, null=False, blank=False)
    next_question = models.ForeignKey(to=DiseaseQuestion, null=True, on_delete=models.SET_NULL)


class DQAnswer(BaseModel):
    panel = models.ForeignKey(to=Panel, on_delete=models.CASCADE, related_name='answers')
    question = ForeignKey(to=DiseaseQuestion, on_delete=models.CASCADE)
    answers = models.ManyToManyField(to=DQChoice)


############################################################################## previously used models end

class Drug(BaseModel):
    doctor = models.ForeignKey(to=Doctor, related_name='drugs', on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(to=Patient, related_name='drugs', on_delete=models.SET_NULL, null=True)
    panel = models.ForeignKey(to=Panel, related_name='drugs', on_delete=models.CASCADE, null=True)
    drug_name = models.CharField(max_length=256, null=True, blank=True)
    consuming_day = models.DateField(default=now)
    consuming_time = models.TimeField(default=now)
    usage_period = models.PositiveIntegerField(null=True)
    numbers = models.PositiveIntegerField(null=True)
    usage = models.CharField(max_length=256, null=True, blank=True)


# class Document(BaseModel):
#     prescription = models.ForeignKey(to=Prescription, on_delete=models.CASCADE, null=False)
#     image = models.ImageField(blank=False, null=False)

############################################################################## previously used models begin

class Notification(BaseModel):
    owner = models.ForeignKey(to=User, null=False, on_delete=models.CASCADE)
    type = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=500, null=False, blank=False)
    body = models.CharField(max_length=500, null=False, blank=False)
    data = JSONField()
    time = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)


############################################################################## previously used models end

#
class HealthEvent(BaseModel):
    owner = models.ForeignKey(to=User, related_name="owning_health_events", null=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, null=True, blank=True)
    invited_patients = models.ManyToManyField(to=Patient, related_name="invited_health_events", blank=True)
    invited_doctors = models.ManyToManyField(to=Doctor, related_name="invited_health_events", blank=True)
    address = models.CharField(max_length=256, null=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True)
    time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(default=now)


class Article(models.Model):
    pub_date = models.DateField(auto_now=True)
    headline = models.CharField(max_length=200)
    content = models.TextField()
    article_picture = models.ImageField(null=True, blank=True)
    reporter = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True)
    tags = TagField()

    def __str__(self):
        return self.headline


class DynamicPanelImageListField(models.Model):
    field_name = models.CharField(max_length=200, unique=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert, force_update, using,
                     update_fields)
        for panel in Panel.objects.all():
            utils.full_panel_with_dynamic_fields(panel)


class BankLogo(BaseModel):
    number = models.CharField(max_length=16)
    name = models.CharField(max_length=50, null=False, blank=False)
    logo = models.ImageField(null=False, blank=False, upload_to='bank_logos/')

    def __str__(self):
        return f'{self.number} - {self.name}'
