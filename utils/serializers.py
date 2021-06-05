from rest_framework import serializers
from authentication.serializers import UserSerializerwithtypeandname
# from utils.costumed_field import Base64ImageField
from utils.models import Image, ImageList

from rest_framework import serializers

from drf_base64.fields import Base64FileField
 #serializers use for conver model data into json data
class ImageSerializer(serializers.ModelSerializer):
    list_id = serializers.IntegerField(write_only=True, required=False)
    file = Base64FileField(
        default=''
    )
    user = UserSerializerwithtypeandname(read_only=True)
    class Meta:
        model = Image
        fields = ['id','user', 'title', 'description', 'file', 'created_date', 'parent', 'list_id','extension']
        read_only_fields = ['parent']

        validators = []
    def create(self, validated_data):
        list_id = validated_data['list_id']
        print(list_id)
        del validated_data['list_id']
        return Image.objects.create(**validated_data, parent_id=list_id)


class ImageSerializerJustIdAndTitle(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'title', ]
        read_only_fields = ['id']


class ImageListSerializer(serializers.ModelSerializer):
    files = ImageSerializer(many=True, required=False)

    class Meta:
        model = ImageList
        fields = ['id', 'title', 'description', 'files']


class ImageListSerializerJustIdAndTitle(serializers.ModelSerializer):
    files = ImageSerializer(many=True, required=False)

    class Meta:
        model = ImageList
        fields = ['id', 'title', 'files']
