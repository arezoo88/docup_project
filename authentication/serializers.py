from rest_framework import serializers

from authentication.models import User, SuggestedDoctor
from utils.costumed_field import Base64ImageField


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # create serializer for convert model data format to json output

        fields = ['username', 'avatar', 'first_name', 'last_name', 'email', 'national_id', 'phone_number', 'credit',
                  'type', 'online']  # these fields will be show in out put
        read_only_fields = ('username', 'phone_number', 'type', 'online', 'credit')  # these fields can not be change.


class BriefUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = ['avatar', 'first_name', 'last_name', 'email', 'type', 'online']
        read_only_fields = ('type', 'online', 'credit')


class BriefBriefUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        read_only_fields = ('credit',)


class BriefBriefUserSerializerWithAvatar(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar']
        read_only_fields = ('credit',)


class SuggestedDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestedDoctor
        fields = "__all__"  # show all fields in output


class ProfileImageSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        max_length=None, use_url=True,
    )
    class Meta:
        model = User
        fields = ('avatar',)

class UserSerializerwithtypeandname(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = ['first_name', 'last_name','type']
        read_only_fields = ('first_name', 'last_name','username','type')  # these fields can not be change.
