from django.db import models

# Create your models here.
from django.db import models
from django.utils.timezone import now

from authentication.models import Patient
from utils.models import BaseModel


class CognitiveTest(BaseModel):
    name = models.CharField(max_length=1000)
    description = models.CharField(max_length=250)
    logo = models.ImageField(null=True,blank=True,upload_to='medical_test_icone')
    TYPE = (
        (0, 'فرم'), (1, 'داخل پنل')
    )
    type = models.IntegerField(choices=TYPE, default=1)
    url = models.CharField(max_length=1000,blank=True,null=True)
    # slug = models.SlugField()

    def __str__(self):
        return self.name
    @property
    def questions_count(self):
        return self.objects.all().count()

class Question(models.Model):
    CognitiveTest = models.ForeignKey(CognitiveTest,related_name='questions',related_query_name='questions', on_delete=models.CASCADE)
    label = models.CharField(max_length=1000)
    TYPE = (
        (0, 'تشریحی'), (1, 'گزینه ای')
    )
    type = models.IntegerField(choices=TYPE, default=1)

    def __str__(self):
        return self.label
    class Meta:
        ordering = ('id',)

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', related_query_name='answers',on_delete=models.CASCADE,null=True,blank=True)
    text = models.CharField(max_length=1000,null=True,blank=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.text

class PatientResponse(models.Model):
    CognitiveTest = models.ForeignKey(CognitiveTest,related_name='responses',related_query_name='responses', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    description = models.CharField(max_length=200,null=True,blank=True)
    Answer = models.ForeignKey(Answer, on_delete=models.CASCADE,null=True,blank=True)
    response_time = models.DateTimeField(default=now)
    screening_step = models.ForeignKey('follow_up.ScreeningSteps', on_delete=models.CASCADE,null=True,blank=True)
    patient = models.ForeignKey(to=Patient, related_name='responses',related_query_name='responses', on_delete=models.SET_NULL, null=True)

