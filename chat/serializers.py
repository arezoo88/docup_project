from rest_framework import serializers

from chat.models import ChatMessage
from drf_base64.fields import Base64FileField


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ('direction', 'modified', 'panel')

class MessageSerializerhttp(serializers.ModelSerializer):
    file = Base64FileField(
        default=''
    )
    class Meta:
        model = ChatMessage
        fields = ['id','panel', 'message', 'message_dirs', 'direction', 'message_types', 'type', 'file','is_read','created_date','modified_date','enabled']
        read_only_fields = ('direction', 'modified', 'panel')
