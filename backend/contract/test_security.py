"""Security regressions run against the real DRF stack, plus PostgreSQL row-lock races."""
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from contract.test_helpers import close_download
from contract.authentication import digest, issue_session, policy
from contract.finance import DOCUMENTS
from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission
from contract.security_models import AuthSession, DownloadGrant, LoginAttempt


PASSWORD = 'Regression-Secure-794!'
LOGIN = '/api/auth/login/'
ME = '/api/auth/me/'
REFRESH = '/api/auth/token/refresh/'
GRANT = '/api/files/grants/'
DOWNLOAD = '/api/files/download/'
SETTINGS = '/api/security-settings/'


def user_for(role, suffix=''):
    user = get_user_model().objects.create_user(username=f'security-{role}{suffix}', password=PASSWORD)
    user.profile.role = Role.objects.get(code=role)
    user.profile.save()
    return user


def login(client, user, remember=False, **headers):
    response = client.post(LOGIN, {'username': user.username, 'password': PASSWORD, 'rememberMe': remember}, format='json', **headers)
    assert response.status_code == 200, response.data
    client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['data']['token']}")
    return response


class SessionSecurityTests(APITestCase):
    def setUp(self):
        self.user = user_for('admin')

    def test_every_role_can_login_me_and_open_its_dashboard(self):
        for role in ['admin', 'dean', 'contract', 'planning', 'finance']:
            user = self.user if role == 'admin' else user_for(role)
            with self.subTest(role=role):
                response = login(self.client, user)
                self.assertEqual(response.data['data']['user']['role']['code'], role)
                self.assertEqual(self.client.get(ME).status_code, 200)
                dashboard = self.client.get('/api/dashboard/')
                self.assertEqual(dashboard.status_code, 200, dashboard.data)
                self.assertEqual(dashboard.data['data']['mode'], role)

    def test_stale_or_malformed_authorization_does_not_break_login(self):
        for header in ['Token', 'Token old', 'Bearer stale']:
            response = login(self.client, self.user, HTTP_AUTHORIZATION=header)
            self.assertTrue(response.data['data']['token'])

    def test_bad_credentials_disabled_user_and_malformed_json_are_controlled(self):
        for payload in [{}, {'username': self.user.username, 'password': 'wrong'}, [], {'username': 'missing', 'password': 'wrong'}]:
            response = self.client.post(LOGIN, payload, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data['status'], 'FAILURE')
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.post(LOGIN, {'username': self.user.username, 'password': PASSWORD}, format='json').status_code, 400)

    def test_bruteforce_lockout_and_successful_reset(self):
        for _ in range(5):
            self.assertEqual(self.client.post(LOGIN, {'username': self.user.username, 'password': 'wrong'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(LOGIN, {'username': self.user.username, 'password': PASSWORD}, format='json').status_code, 429)
        LoginAttempt.objects.update(locked_until=timezone.now() - timedelta(seconds=1))
        login(self.client, self.user)
        self.assertFalse(LoginAttempt.objects.exists())

    def test_access_and_refresh_are_hashed_and_cookies_are_private(self):
        response = login(self.client, self.user, remember=True)
        data = response.data['data']
        session = AuthSession.objects.get()
        self.assertEqual(session.access_hash, digest(data['token']))
        self.assertEqual(session.refresh_hash, digest(response.cookies['cm_refresh'].value))
        self.assertNotIn('refresh', data)
        self.assertNotIn('password', data['user'])
        for name in ['cm_refresh', 'cm_refresh_csrf']:
            cookie = response.cookies[name]
            self.assertTrue(cookie['httponly'])
            self.assertEqual(cookie['samesite'], 'Lax')
            self.assertEqual(cookie['path'], '/api/auth/')
            self.assertTrue(cookie['max-age'])
        self.assertEqual(response['Cache-Control'], 'no-store')
        secure = login(self.client, self.user, HTTP_X_FORWARDED_PROTO='https')
        self.assertTrue(secure.cookies['cm_refresh']['secure'])

    def test_access_expiry_refresh_rotation_and_old_cookie_replay(self):
        response = login(self.client, self.user)
        old_access = response.data['data']['token']
        old_refresh = response.cookies['cm_refresh'].value
        csrf = response.data['data']['csrfToken']
        AuthSession.objects.update(access_expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(ME).status_code, 401)
        refreshed = self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF=csrf)
        self.assertEqual(refreshed.status_code, 200, refreshed.data)
        self.assertNotEqual(old_access, refreshed.data['data']['token'])
        self.assertNotEqual(old_refresh, refreshed.cookies['cm_refresh'].value)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {refreshed.data['data']['token']}")
        self.assertEqual(self.client.get(ME).status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {old_access}')
        self.assertEqual(self.client.get(ME).status_code, 401)
        self.client.cookies['cm_refresh'] = old_refresh
        replay = self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF=refreshed.data['data']['csrfToken'])
        self.assertEqual(replay.status_code, 401)

    def test_refresh_requires_csrf_and_trusted_origin(self):
        response = login(self.client, self.user)
        self.assertEqual(self.client.post(REFRESH, {}, format='json').status_code, 403)
        self.assertEqual(self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF='wrong').status_code, 403)
        csrf = response.data['data']['csrfToken']
        self.assertEqual(self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF=csrf, HTTP_ORIGIN='https://evil.example').status_code, 403)
        self.assertEqual(self.client.post(LOGIN, {'username': self.user.username, 'password': PASSWORD}, format='json', HTTP_ORIGIN='https://evil.example').status_code, 403)
        csrf_response = self.client.get('/api/auth/csrf/')
        self.assertEqual(csrf_response.status_code, 200)
        self.assertEqual(self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF=csrf_response.data['data']['csrfToken']).status_code, 200)

    def test_cors_preflight_allows_security_headers_and_credentials(self):
        response = self.client.options(GRANT, HTTP_ORIGIN='https://cm-dev.svuonline.edu.sy',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST', HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type,x-refresh-csrf,x-download-grant')
        self.assertEqual(response.status_code, 200)
        for header in ['authorization', 'x-refresh-csrf', 'x-download-grant']:
            self.assertIn(header, response['Access-Control-Allow-Headers'].lower())
        self.assertEqual(response['Access-Control-Allow-Origin'], 'https://cm-dev.svuonline.edu.sy')
        self.assertEqual(response['Access-Control-Allow-Credentials'], 'true')

    def test_logout_revokes_current_session_and_refresh_cookie(self):
        response = login(self.client, self.user)
        csrf = response.data['data']['csrfToken']
        self.assertEqual(self.client.post('/api/auth/logout/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.get(ME).status_code, 401)
        self.assertEqual(self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF=csrf).status_code, 403)
        self.assertIsNotNone(AuthSession.objects.get().revoked_at)

    def test_expired_session_cannot_refresh(self):
        response = login(self.client, self.user)
        AuthSession.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.client.get(ME).status_code, 401)
        self.assertEqual(self.client.post(REFRESH, {}, format='json', HTTP_X_REFRESH_CSRF=response.data['data']['csrfToken']).status_code, 401)

    def test_remember_settings_and_session_policy_shortening(self):
        ordinary = login(self.client, self.user)
        self.assertFalse(ordinary.cookies['cm_refresh']['max-age'])
        rules = policy(); rules.allow_remember = False; rules.save()
        response = login(self.client, self.user, remember=True)
        self.assertFalse(response.cookies['cm_refresh']['max-age'])
        self.assertFalse(AuthSession.objects.get(access_hash=digest(response.data['data']['token'])).remembered)
        session = AuthSession.objects.get(access_hash=digest(response.data['data']['token']))
        AuthSession.objects.filter(pk=session.pk).update(created_at=timezone.now() - timedelta(hours=2))
        rules.session_hours = 1; rules.save()
        self.assertEqual(self.client.get(ME).status_code, 401)

    def test_security_settings_are_admin_only_and_validate_bounds(self):
        login(self.client, self.user)
        self.assertEqual(self.client.get(SETTINGS).data['data']['downloadSeconds'], 60)
        for payload in [{'downloadSeconds': 0}, {'downloadSeconds': 3601}, {'accessMinutes': 61}, {'sessionHours': -1}, {'rememberDays': 91}, {'unknown': 7}]:
            self.assertEqual(self.client.patch(SETTINGS, payload, format='json').status_code, 400)
        response = self.client.patch(SETTINGS, {'downloadSeconds': 120, 'accessMinutes': 10, 'sessionHours': 4, 'rememberDays': 3, 'allowRemember': False}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['downloadSeconds'], 120)
        for role in ['dean', 'finance', 'contract', 'planning']:
            login(self.client, user_for(role))
            self.assertEqual(self.client.get(SETTINGS).status_code, 403)
            self.assertEqual(self.client.patch(SETTINGS, {'downloadSeconds': 60}, format='json').status_code, 403)

    def test_password_change_rotates_session_and_revokes_other_devices(self):
        other = APIClient(); login(other, self.user)
        response = login(self.client, self.user)
        changed = self.client.post('/api/auth/change-password/', {'currentPassword': PASSWORD,
            'newPassword': 'Replacement-Strong-652!', 'newPassword2': 'Replacement-Strong-652!'}, format='json')
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(other.get(ME).status_code, 401)
        self.assertEqual(self.client.get(ME).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {changed.data['data']['token']}")
        self.assertEqual(self.client.get(ME).status_code, 200)
        self.assertEqual(AuthSession.objects.filter(revoked_at__isnull=True).count(), 1)

    def test_admin_reset_and_deactivation_revoke_user_sessions(self):
        target = user_for('contract'); other = APIClient(); login(other, target)
        login(self.client, self.user)
        response = self.client.patch(f'/api/auth/users/{target.pk}/', {'resetPassword': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(other.get(ME).status_code, 401)
        target.refresh_from_db()
        _, token, _ = issue_session(target)
        other.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(other.get(ME).status_code, 200)
        response = self.client.patch(f'/api/auth/users/{target.pk}/', {'isActive': False}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(other.get(ME).status_code, 401)


class DownloadSecurityTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='secure-download-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable(); self.addCleanup(settings.disable)
        self.user = user_for('contract')
        login(self.client, self.user)
        self.records = {}
        self.orders = {}
        for kind, (model, relation, filters, _) in DOCUMENTS.items():
            name = 'agreement_name' if kind == 'lifelong-learning' else 'name'
            record = model.objects.create(**filters, **{name: kind}, agreement_number='SEC-' + kind,
                start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                file=SimpleUploadedFile('agreement.txt', b'agreement content'))
            self.records[kind] = record
            self.orders[kind] = DisbursementOrder.objects.create(**{relation: record},
                file=SimpleUploadedFile('order.txt', b'order content'), file_name='order.txt', file_size=13)

    def mint(self, kind='nafath-centers', order=False, scope='agreement', client=None):
        return (client or self.client).post(GRANT, {'kind': kind, 'agreementId': self.records[kind].pk,
            'scope': scope, 'orderId': self.orders[kind].pk if order else None}, format='json')

    def download(self, token, client=None):
        return (client or self.client).get(DOWNLOAD, HTTP_X_DOWNLOAD_GRANT=token)

    def grant(self, **kwargs):
        response = self.mint(**kwargs)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['data']['expiresIn'], 60)
        self.assertNotIn('/media/', str(response.data))
        self.assertNotIn('grant=', response.data['data']['downloadUrl'])
        return response.data['data']['grant']

    def test_all_five_document_types_and_their_orders_download_as_attachments_once(self):
        for kind in DOCUMENTS:
            for order in [False, True]:
                with self.subTest(kind=kind, order=order):
                    token = self.grant(kind=kind, order=order)
                    response = self.download(token)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(b''.join(response.streaming_content), b'order content' if order else b'agreement content')
                    self.assertIn('attachment;', response['Content-Disposition'])
                    self.assertEqual(response['Content-Type'], 'application/octet-stream')
                    self.assertEqual(response['Cache-Control'], 'private, no-store')
                    self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
                    close_download(response)
                    self.assertEqual(self.download(token).status_code, 409)

    def test_expired_and_tampered_links_are_rejected(self):
        token = self.grant()
        DownloadGrant.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.download(token).status_code, 410)
        self.assertEqual(self.download(token + 'broken').status_code, 403)
        self.assertEqual(self.download('invalid').status_code, 403)
        self.assertEqual(self.client.get(DOWNLOAD).status_code, 403)
        self.assertEqual(self.client.get(DOWNLOAD, {'grant': token}).status_code, 403)

    def test_grant_is_bound_to_user_and_session(self):
        token = self.grant()
        other = APIClient(); login(other, user_for('contract', '-other'))
        self.assertEqual(self.download(token, other).status_code, 403)
        second = APIClient(); login(second, self.user)
        self.assertEqual(self.download(token, second).status_code, 403)
        response = self.download(token)
        self.assertEqual(response.status_code, 200); close_download(response)

    def test_permission_revocation_is_checked_again_on_download(self):
        token = self.grant()
        RolePermission.objects.filter(role=self.user.profile.role, feature='nafath-centers').update(can_download=False)
        self.assertEqual(self.mint().status_code, 403)
        self.assertEqual(self.download(token).status_code, 403)
        self.assertIsNone(DownloadGrant.objects.get(token_hash=digest(token)).used_at)
        self.assertEqual(self.client.get('/api/nafath-center/').status_code, 200)

    def test_download_does_not_require_write_and_read_alone_does_not_grant_download(self):
        login(self.client, user_for('finance'))
        RolePermission.objects.filter(role__code='finance', feature='finance').update(can_write=False, can_read=True, can_download=True)
        token = self.grant(scope='finance', order=True)
        response = self.download(token); self.assertEqual(response.status_code, 200); close_download(response)
        RolePermission.objects.filter(role__code='finance', feature='finance').update(can_download=False)
        self.assertEqual(self.mint(scope='finance', order=True).status_code, 403)
        self.assertEqual(self.client.get('/api/finance/agreements/').status_code, 200)

    def test_hidden_documents_are_blocked_for_planning_in_every_scope(self):
        record = self.records['nafath-centers']; record.is_hidden = True; record.save()
        login(self.client, user_for('planning'))
        self.assertEqual(self.mint(scope='planning').status_code, 404)
        self.assertEqual(self.mint(scope='agreement').status_code, 404)
        login(self.client, user_for('admin'))
        self.assertEqual(self.mint(scope='planning').status_code, 404)
        token = self.grant(scope='dean'); response = self.download(token)
        self.assertEqual(response.status_code, 200); close_download(response)

    def test_visibility_changed_after_grant_blocks_planning_download(self):
        login(self.client, user_for('planning'))
        token = self.grant(scope='planning')
        record = self.records['nafath-centers']; record.is_hidden = True; record.save()
        self.assertEqual(self.download(token).status_code, 404)

    def test_changed_removed_missing_and_mismatched_files_cannot_be_downloaded(self):
        token = self.grant(order=True)
        order = self.orders['nafath-centers']; order.title = 'Changed'; order.save()
        self.assertEqual(self.download(token).status_code, 409)
        token = self.grant(order=True)
        order.is_removed = True; order.save()
        self.assertEqual(self.download(token).status_code, 404)
        self.assertEqual(self.mint(order=True).status_code, 404)
        record = self.records['nafath-centers']
        token = self.grant()
        record.file.storage.delete(record.file.name)
        self.assertEqual(self.download(token).status_code, 404)
        self.assertEqual(self.client.post(GRANT, {'kind': 'memorandum', 'agreementId': record.pk,
            'orderId': self.orders['educational-content'].pk}, format='json').status_code, 404)

    def test_unauthenticated_invalid_and_head_requests_do_not_consume_grants(self):
        token = self.grant()
        other = APIClient()
        self.assertEqual(self.download(token, other).status_code, 401)
        self.assertEqual(other.post(GRANT, {}, format='json').status_code, 401)
        self.assertEqual(self.client.head(DOWNLOAD, HTTP_X_DOWNLOAD_GRANT=token).status_code, 405)
        self.assertIsNone(DownloadGrant.objects.get(token_hash=digest(token)).used_at)
        for payload in [{}, [], {'kind': 'nafath-centers', 'agreementId': -1},
                        {'kind': 'invalid', 'agreementId': 1}, {'kind': 'nafath-centers', 'agreementId': 1, 'scope': 'other'},
                        {'kind': 'nafath-centers', 'agreementId': 1, 'file': '/etc/passwd'}]:
            self.assertIn(self.client.post(GRANT, payload, format='json').status_code, [400, 403, 404])

    def test_logout_password_reset_and_account_deactivation_invalidate_grants(self):
        for change in ['logout', 'password', 'deactivate']:
            with self.subTest(change=change):
                self.user.is_active = True; self.user.set_password(PASSWORD); self.user.save()
                login(self.client, self.user)
                token = self.grant()
                if change == 'logout':
                    self.client.post('/api/auth/logout/', {}, format='json')
                elif change == 'password':
                    self.user.set_password('Other-password-93!'); self.user.save()
                else:
                    self.user.is_active = False; self.user.save()
                self.assertEqual(self.download(token).status_code, 401)

    def test_policy_shortening_and_key_rotation_invalidate_existing_grants(self):
        token = self.grant()
        DownloadGrant.objects.update(created_at=timezone.now() - timedelta(seconds=10))
        rules = policy(); rules.download_seconds = 5; rules.save()
        self.assertEqual(self.download(token).status_code, 410)
        token = self.mint().data['data']['grant']
        with override_settings(FILE_DOWNLOAD_SIGNING_KEY='replacement-server-signing-key'):
            self.assertEqual(self.download(token).status_code, 403)

    def test_responses_do_not_expose_storage_paths(self):
        for url in ['/api/nafath-center/', '/api/life-long/', '/api/educational-contents', '/api/other-agreement/', '/api/memorandum/']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            for item in response.data['data']:
                self.assertTrue(item['hasFile'])
                for forbidden in ['file', 'fileUrl', 'storedName']:
                    self.assertNotIn(forbidden, item)
                self.assertNotIn('/media/', str(item))
        for path in ['/media/nafath/secret.pdf', '/media/private/order.txt']:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_legacy_download_routes_also_require_grants(self):
        kind = 'nafath-centers'; pk = self.records[kind].pk; order = self.orders[kind].pk
        urls = [f'/api/agreement-orders/{kind}/{pk}/{order}/file/']
        login(self.client, user_for('admin'))
        urls += [f'/api/{scope}/agreements/{kind}/{pk}/orders/{order}/file/' for scope in ['finance', 'dean']]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_role_permission_invariants_preserve_read_and_separate_download(self):
        login(self.client, user_for('admin'))
        url = '/api/auth/access-control/'
        payload = {'roleCode': 'contract', 'feature': 'nafath-centers', 'download': False}
        self.assertEqual(self.client.patch(url, payload, format='json').status_code, 200)
        permission = RolePermission.objects.get(role__code='contract', feature='nafath-centers')
        self.assertTrue(permission.can_read); self.assertTrue(permission.can_write); self.assertFalse(permission.can_download)
        self.client.patch(url, {**payload, 'read': False}, format='json')
        permission.refresh_from_db()
        self.assertFalse(permission.can_read); self.assertFalse(permission.can_write); self.assertFalse(permission.can_download)
        self.client.patch(url, {**payload, 'download': True}, format='json')
        permission.refresh_from_db()
        self.assertTrue(permission.can_read); self.assertFalse(permission.can_write); self.assertTrue(permission.can_download)
        self.assertEqual(self.client.patch(url, {**payload, 'download': 'false'}, format='json').status_code, 400)


@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL row locking; run with USE_SQLITE_FOR_TESTS=False.')
class ConcurrentDownloadTests(TransactionTestCase):
    def test_only_one_concurrent_request_consumes_the_grant(self):
        directory = tempfile.TemporaryDirectory(prefix='grant-race-')
        self.addCleanup(directory.cleanup)
        with override_settings(MEDIA_ROOT=directory.name):
            user = user_for('contract', '-race')
            model = DOCUMENTS['nafath-centers'][0]
            record = model.objects.create(name='Race', agreement_number='RACE-1', file=SimpleUploadedFile('race.txt', b'race'))
            client = APIClient(); response = login(client, user)
            access = response.data['data']['token']
            grant = client.post(GRANT, {'kind': 'nafath-centers', 'agreementId': record.pk}, format='json').data['data']['grant']
            barrier = Barrier(2)

            def consume():
                close_old_connections()
                try:
                    current = APIClient(); current.credentials(HTTP_AUTHORIZATION=f'Token {access}')
                    barrier.wait(timeout=10)
                    response = current.get(DOWNLOAD, HTTP_X_DOWNLOAD_GRANT=grant)
                    if response.status_code == 200:
                        b''.join(response.streaming_content); response.close()
                    return response.status_code
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: consume(), range(2)))
            self.assertEqual(sorted(results), [200, 409])
