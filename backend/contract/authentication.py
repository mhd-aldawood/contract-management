import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, Throttled

from contract.security_models import AuthSession, LoginAttempt, SecurityPolicy


REFRESH_COOKIE = 'cm_refresh'
CSRF_COOKIE = 'cm_refresh_csrf'


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def policy():
    return SecurityPolicy.objects.get_or_create(pk=1)[0]


def session_valid(session, rules=None):
    rules = rules or policy()
    now = timezone.now()
    duration = timedelta(days=rules.remember_days) if session.remembered and rules.allow_remember else timedelta(hours=rules.session_hours)
    return (not session.revoked_at and session.user.is_active
            and session.password_fingerprint == session.user.get_session_auth_hash()
            and now < min(session.expires_at, session.created_at + duration))


def rotate_access(session, rules):
    access = secrets.token_urlsafe(32)
    session.access_hash = digest(access)
    session.access_issued_at = timezone.now()
    session.access_expires_at = min(session.access_issued_at + timedelta(minutes=rules.access_minutes), session.expires_at)
    return access


def issue_session(user, remembered=False):
    rules = policy()
    remembered = bool(remembered and rules.allow_remember)
    duration = timedelta(days=rules.remember_days) if remembered else timedelta(hours=rules.session_hours)
    refresh = secrets.token_urlsafe(48)
    session = AuthSession(user=user, remembered=remembered, refresh_hash=digest(refresh),
                          password_fingerprint=user.get_session_auth_hash(), expires_at=timezone.now() + duration)
    access = rotate_access(session, rules)
    session.save()
    return session, access, refresh


class SessionTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b'token':
            raise AuthenticationFailed('Invalid authentication header.')
        try:
            key = parts[1].decode('ascii')
        except UnicodeError:
            raise AuthenticationFailed('Invalid token.')
        if not 32 <= len(key) <= 128:
            raise AuthenticationFailed('Invalid token.')
        session = AuthSession.objects.select_related('user', 'user__profile__role').filter(access_hash=digest(key)).first()
        rules = policy()
        if not session or not session_valid(session, rules):
            raise AuthenticationFailed('Session expired. Please sign in again.')
        if timezone.now() >= min(session.access_expires_at, session.access_issued_at + timedelta(minutes=rules.access_minutes)):
            raise AuthenticationFailed('Access token expired.')
        return session.user, session

    def authenticate_header(self, request):
        return 'Token'


def validate_origin(request):
    origin = request.headers.get('Origin')
    referer = request.headers.get('Referer')
    if not origin and referer:
        parsed = urlsplit(referer)
        origin = f'{parsed.scheme}://{parsed.netloc}'
    if origin:
        own = request.build_absolute_uri('/').rstrip('/')
        allowed = set(settings.CORS_ALLOWED_ORIGINS) | set(settings.CSRF_TRUSTED_ORIGINS) | {own}
        if origin not in allowed:
            raise PermissionDenied('Untrusted request origin.')


def validate_refresh_csrf(request):
    validate_origin(request)
    cookie = request.COOKIES.get(CSRF_COOKIE, '')
    header = request.headers.get('X-Refresh-CSRF', '')
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise PermissionDenied('Refresh CSRF validation failed.')


def set_session_cookies(response, request, session, refresh):
    csrf = secrets.token_urlsafe(32)
    max_age = max(1, int((session.expires_at - timezone.now()).total_seconds())) if session.remembered else None
    for name, value in [(REFRESH_COOKIE, refresh), (CSRF_COOKIE, csrf)]:
        response.set_cookie(name, value, max_age=max_age, path='/api/auth/',
                            secure=request.is_secure(), httponly=True, samesite='Lax')
    response.data['data']['csrfToken'] = csrf
    response['Cache-Control'] = 'no-store'
    return response


def clear_session_cookies(response):
    for name in [REFRESH_COOKIE, CSRF_COOKIE]:
        response.delete_cookie(name, path='/api/auth/', samesite='Lax')
    response['Cache-Control'] = 'no-store'
    return response


def check_login_limit(username):
    attempt = LoginAttempt.objects.filter(pk=digest(username.casefold())).first()
    if attempt and attempt.locked_until and attempt.locked_until > timezone.now():
        raise Throttled(wait=max(1, int((attempt.locked_until - timezone.now()).total_seconds())), detail='Too many login attempts. Try again later.')


def failed_login(username):
    now = timezone.now()
    with transaction.atomic():
        attempt, _ = LoginAttempt.objects.select_for_update().get_or_create(
            pk=digest(username.casefold()), defaults={'window_started_at': now})
        if attempt.window_started_at < now - timedelta(minutes=15):
            attempt.failures = 0
            attempt.window_started_at = now
            attempt.locked_until = None
        attempt.failures += 1
        if attempt.failures >= 5:
            attempt.locked_until = now + timedelta(minutes=15)
        attempt.save()
