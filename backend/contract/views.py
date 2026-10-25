
import secrets

from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from django.core.validators import validate_slug
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .api.responses import success_response
from .models import Profile, Role, RolePermission
from .rbac import FEATURES, FEATURE_CODES, IsAdminRole
from .serializers import (
    LoginSerializer,
    UserSerializer,
    TokenSerializer,
    ChangePasswordSerializer,
)


class LoginView(APIView):
    """POST /api/auth/login/  ->  authenticate + return token"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)

        return success_response(
            request=request,
            code='auth.login.success',
            data={
                'user': UserSerializer(user).data,
                'token': token.key,
            },
            status_code=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """POST /api/auth/logout/  ->  delete user's token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        django_logout(request)
        return success_response(
            request=request,
            code='auth.logout.success',
            status_code=status.HTTP_200_OK,
        )


class MeView(APIView):
    """GET /api/auth/me/  ->  current user's info"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            request=request,
            code='auth.me.success',
            data=UserSerializer(request.user).data,
        )


class TokenRefreshView(APIView):
    """POST /api/auth/token/refresh/  ->  rotate token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return success_response(
            request=request,
            code='auth.token_refreshed',
            data=TokenSerializer(token).data,
            status_code=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['newPassword'])
        request.user.save(update_fields=['password'])
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.must_change_password = False
        profile.save(update_fields=['must_change_password'])
        return success_response(
            request=request,
            code='auth.password_changed',
            data=UserSerializer(request.user).data,
        )


def _temporary_password():
    return f"Cm!{secrets.token_urlsafe(12)}"


def _role_or_error(role_code):
    role = Role.objects.filter(code=role_code).first()
    if role is None:
        raise ValidationError({'roleCode': ['Role not found.']})
    return role


class UserManagementView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = User.objects.select_related('profile__role').order_by('username')
        query = request.query_params.get('q', '').strip()
        role_code = request.query_params.get('role', '').strip()
        active = request.query_params.get('active', '').strip().lower()

        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )
        if role_code:
            queryset = queryset.filter(profile__role__code=role_code)
        if active in {'true', 'false'}:
            queryset = queryset.filter(is_active=active == 'true')

        data = UserSerializer(queryset, many=True).data
        return success_response(
            request=request,
            code='user_management.retrieved',
            data=data,
            total_count=len(data),
            page_size=len(data),
        )

    def post(self, request):
        username = str(request.data.get('username', '')).strip()
        email = str(request.data.get('email', '')).strip()
        role_code = str(request.data.get('roleCode', '')).strip()

        errors = {}
        if not username:
            errors['username'] = ['Username is required.']
        elif User.objects.filter(username__iexact=username).exists():
            errors['username'] = ['Username already exists.']
        if email and User.objects.filter(email__iexact=email).exists():
            errors['email'] = ['Email already exists.']
        if not role_code:
            errors['roleCode'] = ['Role is required.']
        if errors:
            raise ValidationError(errors)

        role = _role_or_error(role_code)
        temporary_password = _temporary_password()
        user = User.objects.create_user(
            username=username,
            email=email,
            password=temporary_password,
            is_active=True,
        )
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
        profile.role = role
        profile.must_change_password = True
        profile.save(update_fields=['role', 'must_change_password'])

        return success_response(
            request=request,
            code='user_management.created',
            data={
                'user': UserSerializer(user).data,
                'temporaryPassword': temporary_password,
            },
            status_code=status.HTTP_201_CREATED,
        )


class UserManagementDetailView(APIView):
    permission_classes = [IsAdminRole]

    @staticmethod
    def _get_user(pk):
        user = User.objects.select_related('profile__role').filter(pk=pk).first()
        if user is None:
            raise ValidationError({'userId': ['User not found.']})
        return user

    def patch(self, request, pk):
        user = self._get_user(pk)
        changed_fields = []

        if 'username' in request.data:
            username = str(request.data.get('username', '')).strip()
            if not username:
                raise ValidationError({'username': ['Username is required.']})
            if User.objects.filter(username__iexact=username).exclude(pk=user.pk).exists():
                raise ValidationError({'username': ['Username already exists.']})
            user.username = username
            changed_fields.append('username')

        if 'email' in request.data:
            email = str(request.data.get('email', '')).strip()
            if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                raise ValidationError({'email': ['Email already exists.']})
            user.email = email
            changed_fields.append('email')

        if 'isActive' in request.data:
            value = request.data.get('isActive')
            if not isinstance(value, bool):
                raise ValidationError({'isActive': ['A boolean value is required.']})
            if not value and user.pk == request.user.pk:
                raise ValidationError({'isActive': ['You cannot deactivate your own account.']})
            if not value and user.is_superuser:
                raise ValidationError({'isActive': ['A superuser cannot be deactivated here.']})
            user.is_active = value
            changed_fields.append('is_active')

        if changed_fields:
            user.save(update_fields=list(dict.fromkeys(changed_fields)))

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user)
        if 'roleCode' in request.data:
            profile.role = _role_or_error(str(request.data.get('roleCode', '')).strip())
            profile.save(update_fields=['role'])

        temporary_password = None
        if request.data.get('resetPassword') is True:
            if user.pk == request.user.pk:
                raise ValidationError({
                    'resetPassword': ['You cannot reset your own password from user management.']
                })
            temporary_password = _temporary_password()
            user.set_password(temporary_password)
            user.save(update_fields=['password'])
            profile.must_change_password = True
            profile.save(update_fields=['must_change_password'])
            Token.objects.filter(user=user).delete()

        if not user.is_active:
            Token.objects.filter(user=user).delete()

        data = {'user': UserSerializer(user).data}
        if temporary_password:
            data['temporaryPassword'] = temporary_password
        return success_response(
            request=request,
            code='user_management.updated',
            data=data,
        )


class AccessControlView(APIView):
    permission_classes = [IsAdminRole]

    @staticmethod
    def _matrix():
        roles = []
        for role in Role.objects.prefetch_related('permissions').all():
            permission_map = {
                permission.feature: {
                    'read': permission.can_read,
                    'write': permission.can_write,
                }
                for permission in role.permissions.all()
            }
            roles.append({
                'id': role.id,
                'code': role.code,
                'name': role.name,
                'permissions': {
                    feature['code']: permission_map.get(
                        feature['code'],
                        {'read': False, 'write': False},
                    )
                    for feature in FEATURES
                },
            })

        return {
            'features': FEATURES,
            'roles': roles,
        }

    def get(self, request):
        return success_response(
            request=request,
            code='access_control.retrieved',
            data=self._matrix(),
        )

    def post(self, request):
        role_code = str(request.data.get('roleCode', '')).strip().lower()
        role_name = str(request.data.get('roleName', '')).strip()
        if not role_code or not role_name:
            raise ValidationError({
                'roleCode': ['Role code is required.'],
                'roleName': ['Role name is required.'],
            })
        try:
            validate_slug(role_code)
        except DjangoValidationError:
            raise ValidationError({
                'roleCode': ['Use lowercase English letters, numbers, hyphens, or underscores.']
            })
        if Role.objects.filter(code=role_code).exists():
            raise ValidationError({'roleCode': ['A role with this code already exists.']})

        role = Role.objects.create(code=role_code, name=role_name)
        RolePermission.objects.bulk_create([
            RolePermission(
                role=role,
                feature=feature['code'],
                can_read=False,
                can_write=False,
            )
            for feature in FEATURES
        ])
        return success_response(
            request=request,
            code='access_control.role_created',
            data=self._matrix(),
            status_code=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        role_code = request.data.get('roleCode')
        feature = request.data.get('feature')
        role_name = request.data.get('roleName')

        if role_name is not None and feature is None:
            if role_code == 'admin':
                raise ValidationError({'roleCode': ['The Admin role cannot be renamed.']})
            role = Role.objects.filter(code=role_code).first()
            if role is None:
                raise ValidationError({'roleCode': ['Role not found.']})
            role_name = str(role_name).strip()
            if not role_name:
                raise ValidationError({'roleName': ['Role name is required.']})
            role.name = role_name
            role.save(update_fields=['name'])
        else:
            if role_code == 'admin':
                raise ValidationError({'roleCode': ['Admin permissions cannot be reduced.']})
            if feature not in FEATURE_CODES:
                raise ValidationError({'feature': ['Unknown feature.']})
            role = Role.objects.filter(code=role_code).first()
            if role is None:
                raise ValidationError({'roleCode': ['Role not found.']})

            can_read = bool(request.data.get('read', False))
            can_write = bool(request.data.get('write', False))
            if can_write:
                can_read = True
            RolePermission.objects.update_or_create(
                role=role,
                feature=feature,
                defaults={
                    'can_read': can_read,
                    'can_write': can_write,
                },
            )

        return success_response(
            request=request,
            code='access_control.updated',
            data=self._matrix(),
        )

    def delete(self, request):
        role_code = str(request.data.get('roleCode', '')).strip().lower()
        if role_code in {'admin', 'dean', 'contract', 'planning', 'finance'}:
            raise ValidationError({
                'roleCode': ['Seeded system roles cannot be deleted.']
            })
        role = Role.objects.filter(code=role_code).first()
        if role is None:
            raise ValidationError({'roleCode': ['Role not found.']})
        role.delete()
        return success_response(
            request=request,
            code='access_control.role_deleted',
            data=self._matrix(),
        )
