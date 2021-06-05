import re
from django.http import Http404
from django.shortcuts import _get_queryset
from random import Random
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
import os
import follow_up.models as model
from utils.models import ImageList


def pop_multiple_fields(d, keys):
    ret = {}
    for key in keys:
        if key in d:
            ret[key] = d[key]
            del d[key]
    return ret


regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'


def is_email(s):
    if re.search(regex, s):
        return True
    return False


def generate_token(user):
    from rest_framework_jwt.settings import api_settings

    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

    payload = jwt_payload_handler(user)
    return jwt_encode_handler(payload)


def generate_digit_code(length=6):
    return Random().randint(pow(10, length - 1), pow(10, length))


def full_panel_with_dynamic_fields(panel):
    """
    we complete a panel with dynamicFiled of panel_image_sets
    we raise exception if panel is not None.
    """
    if not panel: raise TypeError
    image_lists_names = set(list(model.DynamicPanelImageListField.objects.values_list('field_name', flat=True)))
    # to be sure we do not add repetitive image_list title
    current_fields_names = set(list(panel.panel_image_sets.values_list('title', flat=True)))
    field_names_should_be_deleted = current_fields_names - image_lists_names
    new_image_list_names_to_be_added = image_lists_names - current_fields_names
    query_set_of_whom_to_be_deleted=panel.panel_image_sets.all().filter(title__in=list(field_names_should_be_deleted))
    panel.panel_image_sets.remove(*list(query_set_of_whom_to_be_deleted))
    for img in query_set_of_whom_to_be_deleted:
        img.delete()
    panel.panel_image_sets.add(*[ImageList.objects.create(title=title) for title in new_image_list_names_to_be_added])
    panel.save()
    return panel


def custom_get_object_or_404(queryset, *filter_args, **filter_kwargs):
    queryset = _get_queryset(queryset)
    if not hasattr(queryset, 'get'):
        klass__name = queryset.__name__ if isinstance(queryset, type) else queryset.__class__.__name__
        raise ValueError(
            "First argument to get_object_or_404() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.get(*filter_args, **filter_kwargs)
    except queryset.model.DoesNotExist:
        raise Http404('ابجت مورد نظر پیدا نشد' % queryset.model._meta.object_name)


@api_view(['GET'])
def get_version(request):
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'version.txt')
    data_file = open(file_path , 'r')
    data = data_file.read()
    return Response(status=HTTP_200_OK, data={'version': data})
