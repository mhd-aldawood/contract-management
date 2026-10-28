from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .rbac import FEATURES, DOWNLOAD_FEATURES, is_admin_user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    rememberMe = serializers.BooleanField(default=False)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled.')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    isAdmin = serializers.SerializerMethodField()
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    isSuperuser = serializers.BooleanField(source='is_superuser', read_only=True)
    mustChangePassword = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'date_joined',
            'role', 'permissions', 'isAdmin',
            'isActive', 'mustChangePassword',
            'isSuperuser',
        ]
        read_only_fields = fields

    def get_role(self, obj):
        role = getattr(getattr(obj, 'profile', None), 'role', None)
        if role is None and obj.is_superuser:
            return {'code': 'admin', 'name': 'Admin'}
        if role is None:
            return None
        return {'code': role.code, 'name': role.name}

    def get_permissions(self, obj):
        if is_admin_user(obj):
            return {
                feature['code']: {'read': True, 'write': True, 'download': feature['code'] in DOWNLOAD_FEATURES}
                for feature in FEATURES
            }

        role = getattr(getattr(obj, 'profile', None), 'role', None)
        permissions = {
            feature['code']: {'read': False, 'write': False, 'download': False}
            for feature in FEATURES
        }
        if role is None:
            return permissions

        for permission in role.permissions.all():
            if permission.feature in permissions:
                permissions[permission.feature] = {
                    'read': permission.can_read,
                    'write': permission.can_write,
                    'download': permission.can_read and permission.can_download,
                }
        return permissions

    def get_isAdmin(self, obj):
        return is_admin_user(obj)

    def get_mustChangePassword(self, obj):
        profile = getattr(obj, 'profile', None)
        return bool(profile and profile.must_change_password)


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(write_only=True, min_length=8)
    newPassword2 = serializers.CharField(write_only=True)

    def validate_currentPassword(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['newPassword'] != attrs['newPassword2']:
            raise serializers.ValidationError({
                'newPassword2': 'Passwords do not match.'
            })
        validate_password(attrs['newPassword'], self.context['request'].user)
        return attrs


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['key', 'created']
