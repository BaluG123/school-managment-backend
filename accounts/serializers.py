from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import HeadmasterProfile, HeadmasterRole


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=HeadmasterRole.choices,
        default=HeadmasterRole.HEADMASTER,
    )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.',
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        phone = validated_data.pop('phone', '')
        role = validated_data.pop('role', HeadmasterRole.HEADMASTER)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=password,
        )
        HeadmasterProfile.objects.create(
            user=user,
            phone=phone,
            role=role,
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='headmaster_profile.phone', read_only=True)
    role = serializers.CharField(source='headmaster_profile.role', read_only=True)
    school_id = serializers.IntegerField(
        source='headmaster_profile.school_id',
        read_only=True,
        allow_null=True,
    )
    school_name = serializers.CharField(
        source='headmaster_profile.school.name',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'school_id', 'school_name',
        ]
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    new_password_confirm = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.',
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
