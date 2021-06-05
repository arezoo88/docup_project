import os
from django.core.exceptions import ValidationError


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    validate_extensions = ['.pdf', '.txt', '.jpg', '.jpeg', '.png', '.xls']
    if not ext.lower() in validate_extensions:
        raise ValidationError('Unsupported file extension.')

def validate_file_size(value):
    limit = 5*1024*1024
    if value.size > limit:
        raise ValidationError('File too large.Size should not exceed 5 MB')
