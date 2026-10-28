import uuid

from django.conf import settings
from django.db import models


class SecurityPolicy(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    download_seconds = models.PositiveIntegerField(default=60)
    access_minutes = models.PositiveIntegerField(default=15)
    session_hours = models.PositiveIntegerField(default=8)
    remember_days = models.PositiveIntegerField(default=7)
    allow_remember = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class AuthSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='secure_sessions')
    access_hash = models.CharField(max_length=64, unique=True)
    refresh_hash = models.CharField(max_length=64, unique=True)
    password_fingerprint = models.CharField(max_length=128)
    remembered = models.BooleanField(default=False)
    access_issued_at = models.DateTimeField()
    access_expires_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DownloadGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AuthSession, on_delete=models.CASCADE, related_name='download_grants')
    token_hash = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=50)
    agreement_id = models.PositiveBigIntegerField()
    order_id = models.PositiveBigIntegerField(null=True, blank=True)
    scope = models.CharField(max_length=20)
    file_version = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoginAttempt(models.Model):
    identity_hash = models.CharField(max_length=64, primary_key=True)
    failures = models.PositiveIntegerField(default=0)
    window_started_at = models.DateTimeField()
    locked_until = models.DateTimeField(null=True, blank=True)
