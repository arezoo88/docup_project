from django.contrib.auth.models import AbstractUser
from django.db import models
from multiselectfield import MultiSelectField
from utils.models import ImageList, Image, BaseModel
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class User(AbstractUser):  # abstract user use for add extra field into user model
    """
        Add new field in user model
    """
    national_id = models.CharField(max_length=10, null=True, blank=False)
    phone_number = models.CharField(max_length=16, null=True, blank=True)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default='0.0')
    user_types = ((0, 'patient'), (1, 'doctor'), (2, 'clinic'))
    type = models.IntegerField(choices=user_types, null=True, blank=False)
    avatar = models.ImageField(null=True, blank=True, upload_to='avatars')
    first_name = models.CharField(_('first name'), max_length=30, null=True, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, null=True, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    verified = models.BooleanField(default=False, )
    online = models.IntegerField(default=0)

class ClinicPlan(BaseModel):
    price = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=100,blank=True,null=True)
    clinic = models.ForeignKey(to='Clinic', null=True, related_name='pclinic', blank=True, on_delete=models.CASCADE)#change




class Clinic(BaseModel):
    user = models.ForeignKey(to=User, null=False, blank=False, on_delete=models.CASCADE, related_name='uclinic')
    SUB_TYPES = ((0, 'بیمارستان'), (1, 'مطب'), (2, 'درمانگاه'))
    sub_type = models.IntegerField(choices=SUB_TYPES, null=True, blank=False)  # with choice created select option in admin panel
    clinic_name = models.CharField(max_length=256, null=True)
    clinic_address = models.CharField(max_length=256, null=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.clinic_name


class WorkTime(BaseModel):
    start_time = models.TimeField()
    end_time = models.TimeField()
    Work_day = models.ForeignKey(to="WorkDay", null=True, blank=True, related_name='work_times',
                                 related_query_name='work_times', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.start_time) + "-" + str(self.end_time)


class WorkDay(BaseModel):
    help_text = f'0-شنبه/1-یکشنبه/2-دوشنبه/3-سه شنبه/4-چهارشنبه/5-پنج شنبه/6-جمعه'
    # day = models.PositiveIntegerField(help_text=help_text,null=True,blank=True)
    date = models.DateField(help_text='date',null=True,blank=True)
    visit_type = models.ForeignKey(to="VisitType", null=True, blank=True, related_name='work_days',
                                   related_query_name='work_days', on_delete=models.CASCADE)
    WEEK_DAYs = {0: 'شنبه', 1: 'یکشنبه', 2: 'دوشنبه', 3: 'سه شنبه', 4: 'چهارشنبه', 5: 'پنجشنبه', 6: 'جمعه'}

    # def convert_day(self):
    #     return self.WEEK_DAYs[self.day]


class VisitType(BaseModel):
    TYPES = ((0, 'حضوری'), (1, 'مجازی'))
    visit_type = models.IntegerField(choices=TYPES, null=False, blank=False)
    METHOD_TYPES = ((0, 'متنی'), (1, 'صوتی'), (2, 'تصویری'))
    visit_method = MultiSelectField(choices=METHOD_TYPES, null=True, blank=True)  # check box  field
    PLANS = ((0, '1۵ دقیقه'), (1, '۳۰ دقیقه'), (2, '۴۵ دقیقه'))
    visit_duration_plan = MultiSelectField(choices=PLANS, null=True, blank=True)
    base_video_price = models.PositiveIntegerField(default=0)
    base_voice_price = models.PositiveIntegerField(default=0)
    base_text_price = models.PositiveIntegerField(default=0)
    base_physical_visit_price = models.PositiveIntegerField(default=0)
    Doctor_supports = models.ForeignKey(to="DoctorSupports", null=True, blank=True, related_name='visit_types',
                                        related_query_name='visit_types', on_delete=models.CASCADE)


class DoctorSupports(BaseModel):
    """
        every doctor has special panel with free time and type visit
    """
    pass


class Doctor(BaseModel):  # inherit from basemodel
    """
     Doctor model
    """
    user = models.ForeignKey(to=User, null=False, blank=False, on_delete=models.CASCADE, related_name='udoctor')
    council_code = models.CharField(max_length=16, null=True, blank=False)
    expert = models.CharField(max_length=32, null=True, blank=False)
    fee = models.IntegerField(null=True)
    account_number = models.CharField(null=True, max_length=16)
    clinic = models.ForeignKey(to=Clinic, null=True, related_name='doctors', blank=False, on_delete=models.CASCADE)
    plan = models.ForeignKey(to=DoctorSupports, null=True, related_name='doctors', blank=True, on_delete=models.CASCADE)
    rate = models.PositiveIntegerField(default=0)


class Patient(BaseModel):  # inherit from basemodel
    """
    patient model
    """
    user = models.ForeignKey(to=User, null=False, blank=False, on_delete=models.CASCADE, related_name='upatient')
    date_of_birth = models.DateField(null=True, blank=True)
    documents = models.ForeignKey(to=ImageList, related_name='documents_owner', null=True,
                                  blank=True, on_delete=models.CASCADE)
    height = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=3, blank=True, null=True)
    user_gender = ((0, 'male'), (1, 'female'))
    gender = models.IntegerField(choices=user_gender, null=True, blank=True)
    birth_location = models.CharField(max_length=50,null=True,blank=True)
    city = models.CharField(max_length=50,null=True,blank=True)
    clinic = models.ForeignKey(to = Clinic,on_delete=models.CASCADE,null=True,blank=True)
    def __str__(self):
        return f'{self.user.first_name }  {self.user.last_name}'

class SuggestedDoctor(BaseModel):
    """
     every user can suggest doctor
    """
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    council_code = models.CharField(max_length=16, null=True, blank=True)
    description = models.CharField(max_length=1000, null=True, blank=True)
    expert = models.CharField(max_length=32, null=True, blank=True)
