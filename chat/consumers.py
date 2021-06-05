import json
import os

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.db.models import Q, F
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404

from authentication.models import Doctor, Patient, User
from chat.models import ChatMessage
from chat.serializers import MessageSerializer,MessageSerializerhttp
from follow_up.models import Panel
from follow_up.tasks import send_async_notification
from django.utils.datetime_safe import datetime

request_types = ("IM_ONLINE", "IM_OFFLINE", "NEW_MESSAGE", "SEND_SEEN", "INIT_RTC","VISIT_REQUEST","TOGGLE_VISIT_TEXT_PLAN")


class ChatConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print(self.scope['username'])
        # self.scope['user'] = get_object_or_404(User, username=self.scope['username'])
        user = self.scope['user']

        print('SALAM',user.first_name)

        if not user.is_authenticated:
            self.close()
            return
        self.panels = Panel.objects.all().filter(
            Q(doctor__user=user) | Q(patient__user=user))

    @staticmethod
    def send_panel_notification(message,request_type,panel_id):
        message["request_type"]=request_type
        channel_layer = get_channel_layer()
        group_name = 'panel_%s' % panel_id
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "chat_message",
                "message": message,
            }

        )

    def prepare_io_nf_message(self, request_type):
        """
        this method prepare IM_ONLINE request type message (io)
        """
        user = self.scope['user']
        message = dict()
        message['request_type'] = request_type
        if user.type == 0:
            message['patient_id'] = get_object_or_404(Patient, user=user).id
        else:
            message['doctor_id'] = get_object_or_404(Doctor, user=user).id
        return message

    def send_ion_message(self):
        """send IM_ONLINE to all groups members"""
        message = self.prepare_io_nf_message("IM_ONLINE")
        for panel in self.panels:
            grp = 'panel_%s' % panel.id
            message['panel_id'] = panel.id
            async_to_sync(self.channel_layer.group_send)(
                grp,
                {
                    'type': 'chat_message',
                    'message': message,
                    'source': self.channel_name
                }
            )

    def send_iof_message(self):
        """send IM_OFFLINE to all groups members"""
        message = self.prepare_io_nf_message("IM_OFFLINE")
        for panel in self.panels:
            grp = 'panel_%s' % panel.id
            message['panel_id'] = panel.id
            async_to_sync(self.channel_layer.group_send)(
                grp,
                {
                    'type': 'chat_message',
                    'message': message,
                    'source': self.channel_name
                }
            )

    def set_online_status(self):
        user = self.scope['user']
        User.objects.filter(id=user.id).update(online=F('online')+1)



    def set_offline_status(self):
        user = self.scope['user']
        User.objects.filter(id=user.id).update(online=F('online') - 1)

    def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            self.close()
            return
        # set user status ONLINE
        self.set_online_status()

        # add user to its panel groups
        for panel in self.panels:
            grp = 'panel_%s' % panel.id
            async_to_sync(self.channel_layer.group_add)(
                grp,
                self.channel_name
            )
        self.accept()
        self.send_ion_message()

    def disconnect(self, close_code):
        # set offline status
        self.set_offline_status()
        # Leave room group
        for panel in self.panels:
            grp = 'panel_%s' % panel.id
            async_to_sync(self.channel_layer.group_discard)(
                grp,
                self.channel_name
            )
        self.send_iof_message()

    def prepare_new_message(self, form_data, instance, direction):
        """ adding necessary data to message to be seen in reception"""
        form_data["message_id"] = instance.id
        form_data["is_read"] = instance.is_read
        form_data["direction"] = direction
        form_data["type"] = instance.type
        form_data["file"] = instance.file
        return form_data

    # Receive message from WebSocket
    def receive(self, text_data=None, bytes_data=None):
        # decode message
        form_data = json.loads(text_data)

        print("********")

        # os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        print(form_data)
        # if form_data.get("request_type"): raise PermissionDenied()
        try:
            visit_text_plan_id = form_data["visit_text_plan_id"]
        except:
            visit_text_plan_id = None
        direction, panel = self.check_permission(form_data["panel_id"],visit_text_plan_id)
        user = self.scope['user']
        if form_data["request_type"] == "NEW_MESSAGE":
            # create message entity in database
            if direction == 0:
                header_info = f' پیام جدید از بیمار {user.first_name} {user.last_name}'
                user_send_msg = get_object_or_404(Panel, pk=form_data["panel_id"]).doctor.user.id
            else:
                header_info = f' پیام جدید از دکتر {user.first_name} {user.last_name}'
                user_send_msg = get_object_or_404(Panel, pk=form_data["panel_id"]).patient.user.id

            if form_data["type"] == 0:
                body_info = form_data["message"]
                send_async_notification.apply_async(args=(header_info, body_info, user_send_msg, {"type": 10, "payload": form_data}, datetime.now(), 10))
                form_data = self.create(form_data, direction, panel)
            else:
                body_info = 'پیام جدید'
                send_async_notification.apply_async(args=(header_info, body_info, user_send_msg, {"type": 10, "payload": form_data}, datetime.now(), 10))
                form_data = self.get_file_in_message(form_data)
            # send to the destination group full message
            # form_data = self.prepare_new_message(form_data, instance, direction)
            form_data["request_type"] = "NEW_MESSAGE"
            form_data["panel_id"] = form_data.pop('panel', None)

        elif form_data["request_type"] == "SEND_SEEN":
            # update is_read field in database
            self.update(form_data, panel, direction)
        elif form_data["request_type"] == "IM_ONLINE" or form_data["request_type"] == "IM_OFFLINE":
            return
        # elif form_data["request_type"] == "TOGGLE_VISIT_TEXT_PLAN":
        #     pass

        # os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "false"

        # Send message to room group
        grp = 'panel_%s' % form_data["panel_id"]
        async_to_sync(self.channel_layer.group_send)(
            grp,
            {
                'type': 'chat_message',
                'message': form_data,
                'source': self.channel_name
            }
        )

    def do_not_echo(self, event):
        source_channel_name = event.get('source')
        request_type = event.get('message').get('request_type')
        if request_type == 'IM_ONLINE' or request_type == 'IM_OFFLINE':
            if self.channel_name == source_channel_name: return True
        if request_type == "INIT_RTC" and self.channel_name == source_channel_name: return True
        return False

    # Receive message from room group
    def chat_message(self, event):
        print("in chat message func ********")
        try:
            message = event['message']
            # do not echo back my message if not necessary
            if self.do_not_echo(event): return
            self.send(text_data=json.dumps(message))
        except Exception:
            self.send(text_data=json.dumps({"sent": False}))

    def update(self, form_data, panel, direction):
        instance = get_object_or_404(ChatMessage.objects.filter(panel=panel), id=form_data['message_id'])
        print(instance.direction)
        print(direction)
        if not instance.direction == direction:
            instance.is_read = True
            instance.save(update_fields=['is_read'])
            return True
        return False

    def get_object(self, panel):
        queryset = ChatMessage.objects.filter(panel=panel)
        obj = get_object_or_404(queryset, panel=panel)
        return obj

    def create(self, data, direction, panel):
        serializer = MessageSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(direction=direction, panel=panel)
        return serializer.data
    def get_file_in_message(self,data):
        queryset = ChatMessage.objects.get(pk=data['message_id'])
        serializer = MessageSerializer(queryset)
        # serializer.is_valid(raise_exception=True)
        # instance = serializer.save(direction=direction, panel=panel)
        return serializer.data

    def check_permission(self, panel_id,visit_text_plan_id):
        panel = get_object_or_404(Panel, pk=panel_id)
        user = self.scope['user']
        if visit_text_plan_id:
            if user.type == 1:
                direction = 1
                if panel.doctor is not None and panel.doctor.user != user:
                    raise PermissionDenied({'detail': "not related panel", "error_code": 606})
            else:
                raise PermissionDenied({'detail':'patient do not have access','error_code':606})

        else:
            if user.type == 0:
                direction = 0
                if panel.patient is not None and panel.patient.user != user:
                    raise PermissionDenied({'detail': "not related panel", "error_code": 606})
            else:
                direction = 1
                if panel.doctor is not None and panel.doctor.user != user:
                    raise PermissionDenied({'detail': "not related panel", "error_code": 606})
        return direction, panel
