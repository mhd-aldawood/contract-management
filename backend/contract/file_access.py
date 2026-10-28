import secrets
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework import serializers
from rest_framework.exceptions import APIException, PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.authentication import digest, policy, session_valid
from contract.finance_models import DisbursementOrder
from contract.rbac import user_has_feature_permission
from contract.security_models import AuthSession, DownloadGrant


class GrantExpired(APIException):
    status_code = 410
    default_detail = 'Download link expired. Request a new link.'


class GrantUsed(APIException):
    status_code = 409
    default_detail = 'Download link was already used or the file changed. Request a new link.'


def signing_key():
    return getattr(settings, 'FILE_DOWNLOAD_SIGNING_KEY', '') or salted_hmac('cm.file-download-key', 'v1').hexdigest()


def resolve_file(user, kind, pk, scope, order_id=None):
    from contract.finance import agreement_scope
    if scope not in {'agreement', 'planning', 'dean', 'finance'}:
        raise PermissionDenied('Invalid document scope.')
    feature = kind if scope == 'agreement' else scope
    if not user_has_feature_permission(user, feature, 'download'):
        raise PermissionDenied('You do not have download permission for this feature.')
    agreement, relation = agreement_scope(kind, pk)
    role = getattr(getattr(user, 'profile', None), 'role', None)
    if (scope == 'planning' or (role and role.code == 'planning')) and agreement.is_hidden:
        raise NotFound()
    instance = get_object_or_404(DisbursementOrder, pk=order_id, is_removed=False, **relation) if order_id is not None else agreement
    if not instance.file:
        raise NotFound()
    filename = (instance.file_name if order_id is not None else getattr(instance, 'original_name', '') or getattr(instance, 'file_name', ''))
    filename = filename or f'{agreement.agreement_number}-document'
    version = digest(f'{instance.file.name}:{instance.updated_at.isoformat()}')
    return instance, filename, version


class GrantRequestSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'non_field_errors': ['Expected a JSON object.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: ['Unknown field.'] for key in unknown})
        return super().to_internal_value(data)

    kind = serializers.CharField(max_length=50)
    agreementId = serializers.IntegerField(min_value=1)
    scope = serializers.ChoiceField(choices=['agreement', 'planning', 'dean', 'finance'], default='agreement')
    orderId = serializers.IntegerField(min_value=1, required=False, allow_null=True)


class DownloadGrantView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not isinstance(request.auth, AuthSession) or not session_valid(request.auth):
            raise PermissionDenied('A valid login session is required.')
        serializer = GrantRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        _, _, version = resolve_file(request.user, data['kind'], data['agreementId'], data['scope'], data.get('orderId'))
        lifetime = policy().download_seconds
        grant = DownloadGrant(session=request.auth, kind=data['kind'], agreement_id=data['agreementId'],
                              order_id=data.get('orderId'), scope=data['scope'], file_version=version,
                              expires_at=min(timezone.now() + timedelta(seconds=lifetime), request.auth.expires_at))
        token = signing.dumps({'id': str(grant.pk), 'nonce': secrets.token_urlsafe(16)}, key=signing_key(), salt='cm.download.v1')
        grant.token_hash = digest(token)
        grant.save()
        response = success_response(request=request, code='request.success', data={
            'grant': token, 'expiresAt': grant.expires_at, 'expiresIn': lifetime,
            'downloadUrl': reverse('secure-download', request=request),
        })
        response['Cache-Control'] = 'no-store'
        return response


def consume_download_grant(request, *, kind=None, pk=None, order_id=None):
    token = request.headers.get('X-Download-Grant', '')
    if not token or len(token) > 2048 or not isinstance(request.auth, AuthSession):
        raise PermissionDenied('A download grant and login session are required.')
    rules = policy()
    try:
        data = signing.loads(token, key=signing_key(), salt='cm.download.v1', max_age=rules.download_seconds)
        grant_id = data['id']
    except signing.SignatureExpired:
        raise GrantExpired()
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        raise PermissionDenied('Invalid download grant.')
    with transaction.atomic():
        session = get_object_or_404(AuthSession.objects.select_for_update(of=('self',)).select_related('user__profile__role'), pk=request.auth.pk)
        if not session_valid(session, rules):
            raise PermissionDenied('This login session is no longer valid.')
        grant = get_object_or_404(DownloadGrant.objects.select_for_update(), pk=grant_id, token_hash=digest(token))
        if grant.session_id != request.auth.pk:
            raise PermissionDenied('This link belongs to another login session.')
        now = timezone.now()
        if now >= min(grant.expires_at, grant.created_at + timedelta(seconds=rules.download_seconds)):
            raise GrantExpired()
        if grant.used_at:
            raise GrantUsed()
        if kind is not None and (grant.kind != kind or grant.agreement_id != pk or grant.order_id != order_id):
            raise PermissionDenied('Download grant does not match this document.')
        instance, filename, version = resolve_file(session.user, grant.kind, grant.agreement_id, grant.scope, grant.order_id)
        if version != grant.file_version:
            raise GrantUsed()
        try:
            stream = instance.file.open('rb')
        except FileNotFoundError:
            raise NotFound()
        claimed = DownloadGrant.objects.filter(pk=grant.pk, used_at__isnull=True).update(used_at=now)
        if claimed != 1:
            stream.close()
            raise GrantUsed()
    response = FileResponse(stream, as_attachment=True, filename=filename, content_type='application/octet-stream')
    response['Cache-Control'] = 'private, no-store'
    response['Pragma'] = 'no-cache'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    response['Referrer-Policy'] = 'no-referrer'
    return response


class SecureDownloadView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'options']

    def get(self, request):
        return consume_download_grant(request)
