
from django.contrib.auth.models import User
from django.contrib.auth import logout as django_logout
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .api.responses import success_response
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    UserSerializer,
    TokenSerializer,
)


class SignupView(APIView):
    """POST /api/auth/signup/  ->  create user + return token"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return success_response(
            request=request,
            code='auth.signup.success',
            data={
                'user': UserSerializer(user).data,
                'token': token.key,
            },
            status_code=status.HTTP_201_CREATED,
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
