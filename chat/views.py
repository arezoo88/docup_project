from django.http import Http404
from django.shortcuts import render
from itertools import chain
# Create your views here.
from operator import attrgetter
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404, UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from chat.models import ChatMessage
from chat.serializers import MessageSerializer,MessageSerializerhttp
from follow_up.models import Panel

"""
this view is depricated


"""
class SendMessageToPanel(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializerhttp
    pagination_class = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.panel = None

    def check_permission(self):
        panel_id = self.kwargs['panel_id']
        panel = get_object_or_404(Panel, pk=panel_id)
        user = self.request.user
        if user.type == 0:
            if panel.patient is not None and panel.patient.user != user:
                raise PermissionDenied({'detail':"not related panel","error_code":606})
        else:
            if panel.doctor is not None and panel.doctor.user != user:
                raise PermissionDenied({'detail':"not related panel","error_code":606})
        self.panel = panel

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # return Response({True}, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.data)

    def perform_create(self, serializer):
        self.check_permission()
        user = self.request.user
        if user.type == 0:  # user is patient
            direction = 0
        else:  # user is doctor
            direction = 1

        serializer.save(direction=direction, panel=self.panel)

    def get_queryset(self):
        self.check_permission()
        return ChatMessage.objects.filter(panel=self.panel)

    def list(self, request, *args, **kwargs):
        self.check_permission()
        user = self.request.user
        if user.type == 0:  # user is patient
            reverse_direction = 1
        else:  # user is doctor
            reverse_direction = 0

        up = request.query_params.get('up')
        down = request.query_params.get('down')
        size = request.query_params.get('size')
        # check it specified necessary params
        if not up or not down or not size: return Response(status=HTTP_200_OK, data={
            'details': '[up] or [down] or [size] can not be null in params'})
        message_id = request.query_params.get('message_id')
        query = self.get_queryset()
        # print(reverse_direction)
        if (not message_id) or message_id == 'null' or message_id == 'null' or message_id == 'none':
            message_id = None

        if not message_id:
            chat_message = query.filter(direction=reverse_direction, is_read=True).order_by('pk').last()
            if not chat_message:
                message_id = 0
            else:
                message_id = chat_message.id

        if int(down) == 1 and int(up) == 1 and message_id == 0:
            query = query.filter(pk__gt=message_id).order_by('-created_date')[:int(size)]
        elif int(down) and int(up):
            query1 = query.filter(pk__gt=message_id).order_by('created_date')[:int(size)]
            query2 = query.filter(pk__lte=message_id).order_by('-created_date')[:int(size)]
            query = chain(query1, query2)
            query=sorted(query,key=attrgetter('created_date'),reverse=True)
        elif int(down):
            query = query.filter(pk__gt=message_id).order_by('created_date')[:int(size)]
        elif int(up):
            query  = query.filter(pk__lte=message_id).order_by('-created_date')[:int(size)]

        queryset = self.filter_queryset(query)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SendLastSeen(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessageSerializer
    pagination_class = None
    lookup_field = 'id'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.panel = None

    def check_permission(self):
        panel_id = self.kwargs['panel_id']
        panel = get_object_or_404(Panel, pk=panel_id)
        user = self.request.user
        if user.type == 0:
            if panel.patient is not None and panel.patient.user != user:
                raise PermissionDenied({'detail':"not related panel","error_code":606})
        else:
            if panel.doctor is not None and panel.doctor.user != user:
                raise PermissionDenied({'detail':"not related panel","error_code":606})
        self.panel = panel

    def perform_update(self, serializer):
        self.check_permission()
        serializer.save()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.request.data[self.lookup_field]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        self.check_permission()
        return ChatMessage.objects.filter(panel=self.panel)

