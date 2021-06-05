from django.db import models

# Create your models here.
from follow_up.models import Panel
from utils.models import BaseModel


class ChatMessage(BaseModel):
    panel = models.ForeignKey(to=Panel,related_name='chats',related_query_name='chats', on_delete=models.SET_NULL, null=True)
    message = models.CharField(max_length=256, null=True, blank=True)

    message_dirs = ((0, 'patient_to_doctor'), (1, 'doctor_to_patient'))
    direction = models.IntegerField(choices=message_dirs, null=False, blank=False)

    message_types = ((0, 'text'), (1, 'image'), (2, 'voice'),(3, 'video'),(4,'pdf'))
    type = models.IntegerField(choices=message_types, default=0, null=False, blank=False)
    file = models.FileField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
