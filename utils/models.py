from django.db import models
from .validators import validate_file_extension,validate_file_size
from django.core.validators import FileExtensionValidator
import os
from django.conf import settings
User = settings.AUTH_USER_MODEL

class BaseModel(models.Model): #other models use this model and inherit from this
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True


class ImageList(BaseModel):
    title = models.CharField(max_length=64, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, blank=True)


class Image(BaseModel):
    user = models.ForeignKey(to=User, null=True,blank=True, on_delete=models.CASCADE)
    parent = models.ForeignKey(to=ImageList, on_delete=models.CASCADE, related_name='files', null=True)
    title = models.CharField(max_length=64, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    file = models.FileField(blank=True, null=True, validators=[FileExtensionValidator(allowed_extensions=['pdf','txt','jpeg','jpg','xls','png']),validate_file_size])
    def extension(self):
        if self.file.name:
            return os.path.splitext(self.file.name)[1]
        return ""

class Voucher(models.Model):#in this model save discount code
    code = models.CharField(max_length=100)
    discount = models.PositiveIntegerField(default=0,help_text='format is percent')
    expire_date = models.DateTimeField(null=True,blank=True)
    enabled = models.BooleanField(default=True)
    def __str__(self):
        return self.code

class City(models.Model):
    city_id=models.PositiveIntegerField()
    city_title = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = 'cities'
    def __str__(self):
        return self.city_title