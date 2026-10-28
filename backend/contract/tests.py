import json
import shutil
import tempfile
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from contract.authentication import issue_session
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

from contract.models import Role


UNIFIED_RESPONSE_KEYS = {
    "status",
    "code",
    "message",
    "data",
    "totalCount",
    "page",
    "pageSize",
}


class AgreementSaveResponseTests(APITestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="contract-api-tests-")
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()

        user = get_user_model().objects.create_user(
            username="api-test-user",
            password="test-password",
        )
        _, token, _ = issue_session(user)
        user.profile.role = Role.objects.get(code="admin")
        user.profile.save(update_fields=["role"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_nafath_save_returns_backend_message_and_file_data(self):
        payload = {
            "type": "nafath-center",
            "agreementNumber": "NF-API-1",
            "name": "اتفاقية نفاذ اختبارية",
            "companyName": "شركة اختبار",
            "subject": "موضوع اختباري للاتفاقية",
            "estimatedCost": "100.00",
            "startDate": "2026-10-11",
            "endDate": "2026-10-12",
            "reminderDate": "2026-10-10",
            "paymentMethod": "text",
            "paymentText": "دفعة واحدة",
            "paymentSchedule": json.dumps([]),
            "status": "نشط",
            "disbursement": "",
            "budgetType": "investment",
            "isHidden": "false",
            "fileName": "agreement.txt",
            "file": SimpleUploadedFile(
                "agreement.txt",
                b"agreement attachment",
                content_type="text/plain",
            ),
        }

        response = self.client.post(
            "/api/nafath-center/create",
            payload,
            format="multipart",
            HTTP_ACCEPT_LANGUAGE="ar",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(response.data["code"], "agreement.nafath.created")
        self.assertEqual(response.data["message"], "تم حفظ اتفاقية مركز نفاذ بنجاح")
        self.assertEqual(response.data["data"]["fileName"], "agreement.txt")
        self.assertEqual(response.data["data"]["reminderDate"], "2026-10-10")
        self.assertTrue(response.data["data"]["hasFile"])
        self.assertTrue(UNIFIED_RESPONSE_KEYS.issubset(response.data))

    def test_lifelong_save_uses_name_and_investment_wire_values(self):
        payload = {
            "type": "life-long",
            "agreementNumber": "LL-API-1",
            "name": "اتفاقية التعلم مدى الحياة",
            "companyName": "شركة اختبار",
            "subject": "موضوع اختباري للاتفاقية",
            "startDate": "2026-10-11",
            "endDate": "2026-10-12",
            "reminderDate": "2026-10-10",
            "paymentMethod": "text",
            "paymentText": "دفعة واحدة",
            "paymentSchedule": json.dumps([]),
            "status": "نشط",
            "disbursement": "",
            "budgetType": "investment",
            "isHidden": "false",
        }

        response = self.client.post(
            "/api/life-long/create",
            payload,
            format="multipart",
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(response.data["code"], "agreement.life_long.created")
        self.assertEqual(
            response.data["message"],
            "Lifelong Learning agreement saved successfully",
        )
        self.assertEqual(response.data["data"]["name"], payload["name"])
        self.assertEqual(response.data["data"]["budgetType"], "investment")
        self.assertEqual(response.data["data"]["reminderDate"], "2026-10-10")
        self.assertTrue(UNIFIED_RESPONSE_KEYS.issubset(response.data))

    def test_educational_content_save_persists_reminder_date(self):
        response = self.client.post(
            "/api/educational-contents",
            {
                "type": "educational-content",
                "agreementNumber": "EDU-API-1",
                "name": "Educational agreement",
                "startDate": "2026-10-11",
                "endDate": "2026-10-12",
                "reminderDate": "2026-10-10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["reminderDate"], "2026-10-10")

    def test_other_agreement_save_persists_reminder_date(self):
        response = self.client.post(
            "/api/other-agreement/create",
            {
                "type": "other-agreements",
                "agreementNumber": "OTHER-API-1",
                "name": "Other agreement",
                "startDate": "2026-10-11",
                "endDate": "2026-10-12",
                "reminderDate": "2026-10-10",
                "rows": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["reminderDate"], "2026-10-10")

    def test_validation_error_uses_failure_envelope(self):
        response = self.client.post(
            "/api/nafath-center/create",
            {"estimatedCost": "not-a-number"},
            format="json",
            HTTP_ACCEPT_LANGUAGE="ar",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "FAILURE")
        self.assertEqual(response.data["code"], "request.validation_failed")
        self.assertIn("estimatedCost", response.data["errors"])
        self.assertIsNone(response.data["data"])
        self.assertEqual(response.data["totalCount"], 0)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["pageSize"], 10)


class ContractListTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='list-admin', password='test-password')
        self.user.profile.role = Role.objects.get(code='admin')
        self.user.profile.save(update_fields=['role'])
        self.client.force_authenticate(self.user)

    def test_each_page_lists_saved_records_and_reminder_dates(self):
        endpoints = [
            ('/api/nafath-center/create', '/api/nafath-center/', 'nafath-center'),
            ('/api/life-long/create', '/api/life-long/', 'life-long'),
            ('/api/educational-contents', '/api/educational-contents', 'educational-content'),
            ('/api/other-agreement/create', '/api/other-agreement/', 'other-agreements'),
            ('/api/memorandum/create', '/api/memorandum/', 'memorandum'),
        ]
        for create_url, list_url, kind in endpoints:
            with self.subTest(kind=kind):
                created = self.client.post(create_url, {
                    'type': kind, 'agreementNumber': f'LIST-{kind}', 'name': 'Saved agreement',
                    'companyName': 'Company', 'startDate': '2026-10-01', 'endDate': '2027-10-01',
                    'reminderDate': '2027-09-01', 'rows': [{'header': 'Clause', 'body': 'Text'}],
                }, format='json')
                self.assertEqual(created.status_code, 201, created.data)
                listed = self.client.get(list_url)
                self.assertEqual(listed.status_code, 200)
                self.assertEqual(len(listed.data['data']), 1)
                self.assertEqual(listed.data['data'][0]['agreementNumber'], f'LIST-{kind}')
                self.assertEqual(listed.data['data'][0]['reminderDate'], '2027-09-01')

    def test_new_lists_require_their_own_feature_permission(self):
        from contract.models import RolePermission
        self.user.profile.role = Role.objects.get(code='finance')
        self.user.profile.save(update_fields=['role'])
        for feature, endpoint in [
            ('lifelong-learning', '/api/life-long/'),
            ('other-agreements', '/api/other-agreement/'),
            ('memorandum', '/api/memorandum/'),
        ]:
            with self.subTest(feature=feature):
                RolePermission.objects.filter(role=self.user.profile.role, feature=feature).update(can_read=False, can_write=False)
                self.assertEqual(self.client.get(endpoint).status_code, 403)

    def test_other_and_memorandum_cannot_cross_feature_boundaries(self):
        from contract.other.models import Agreement
        response = self.client.post('/api/other-agreement/create', {
            'type': 'memorandum', 'agreementNumber': 'TYPE-BOUNDARY', 'name': 'Agreement',
            'startDate': '2026-10-01', 'endDate': '2027-10-01',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Agreement.objects.get().type, 'other-agreements')
        self.assertEqual(self.client.get('/api/memorandum/').data['data'], [])


class PlanningAgreementTests(APITestCase):
    endpoint = '/api/planning/agreements/'

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='planning-reader', password='test-password')
        self.user.profile.role = Role.objects.get(code='planning')
        self.user.profile.save(update_fields=['role'])
        self.client.force_authenticate(self.user)
        self.today = date(2026, 10, 25)
        clock = patch('contract.planning.planning_today', return_value=self.today)
        clock.start()
        self.addCleanup(clock.stop)

    def create_nafath(self, number, start, end, hidden=False):
        from contract.nafath_center.models import NafathCenterAgreement
        return NafathCenterAgreement.objects.create(
            agreement_number=number, name=number, company_name='Company',
            start_date=start, end_date=end, is_hidden=hidden, status='manual status',
        )

    def test_date_classification_and_filters_include_today(self):
        yesterday = self.today - timedelta(days=1)
        tomorrow = self.today + timedelta(days=1)
        cases = [
            ('finished', yesterday, yesterday, 'finish'),
            ('current', yesterday, tomorrow, 'current'),
            ('future', tomorrow, tomorrow, 'future'),
            ('starts-today', self.today, tomorrow, 'current'),
            ('ends-today', yesterday, self.today, 'current'),
            ('today-only', self.today, self.today, 'current'),
            ('missing-date', None, tomorrow, 'unknown'),
            ('reversed-dates', tomorrow, yesterday, 'unknown'),
        ]
        for number, start, end, _ in cases:
            self.create_nafath(number, start, end)
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item['agreementNumber']: item['planningPhase'] for item in response.data['data']},
                         {number: phase for number, _, _, phase in cases})
        self.assertTrue(all(item['status'] == 'manual status' for item in response.data['data']))
        for phase in ['finish', 'current', 'future', 'unknown']:
            with self.subTest(phase=phase):
                filtered = self.client.get(self.endpoint, {'phase': phase})
                self.assertEqual({item['agreementNumber'] for item in filtered.data['data']},
                                 {number for number, _, _, expected in cases if expected == phase})
                self.assertEqual(filtered.data['totalCount'], len(filtered.data['data']))

    def test_all_document_types_exclude_hidden_for_planning_and_admin(self):
        from contract.educational_content.models import EducationalContent
        from contract.life_long.models import LifeLongAgreement
        from contract.other.models import Agreement
        from contract.models import RolePermission
        self.create_nafath('visible-nafath', self.today, self.today)
        hidden_nafath = self.create_nafath('hidden-nafath', self.today, self.today, hidden=True)
        for model, kind, name_field in [
            (LifeLongAgreement, 'life-long', 'agreement_name'),
            (EducationalContent, 'educational-content', 'name'),
            (Agreement, 'other-agreements', 'name'),
            (Agreement, 'memorandum', 'name'),
        ]:
            for hidden in [False, True]:
                model.objects.create(type=kind, agreement_number=f'{kind}-{hidden}',
                                     **{name_field: kind}, start_date=self.today,
                                     end_date=self.today, is_hidden=hidden)

        # Planning permission grants its consolidated visible list without requiring
        # separate access to the contract creation/management pages.
        RolePermission.objects.filter(role=self.user.profile.role).exclude(feature='planning').update(can_read=False, can_write=False)
        for role in ['planning', 'admin']:
            self.user.profile.role = Role.objects.get(code=role)
            self.user.profile.save(update_fields=['role'])
            response = self.client.get(self.endpoint, {'isHidden': 'true'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['totalCount'], 5)
            self.assertEqual(len({item['feature'] for item in response.data['data']}), 5)
            self.assertTrue(all(item['isHidden'] is False for item in response.data['data']))

        # Clearing Hide makes the same document appear on the next list refresh.
        hidden_nafath.is_hidden = False
        hidden_nafath.save(update_fields=['is_hidden'])
        self.assertEqual(self.client.get(self.endpoint).data['totalCount'], 6)

    def test_planning_permission_and_authentication_are_required(self):
        from contract.models import RolePermission
        RolePermission.objects.filter(role=self.user.profile.role, feature='planning').update(can_read=False, can_write=False)
        self.assertEqual(self.client.get(self.endpoint).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)

    def test_invalid_phase_is_rejected(self):
        self.assertEqual(self.client.get(self.endpoint, {'phase': 'invalid'}).status_code, 400)


class AuthUnifiedResponseTests(APITestCase):
    def test_login_uses_the_unified_response(self):
        get_user_model().objects.create_user(
            username="unified-user",
            email="unified@example.com",
            password="Strong-test-password-123!",
        )

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "username": "unified-user",
                "password": "Strong-test-password-123!",
            },
            format="json",
            HTTP_ACCEPT_LANGUAGE="ar",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertEqual(login_response.data["status"], "SUCCESS")
        self.assertEqual(login_response.data["code"], "auth.login.success")
        self.assertEqual(login_response.data["message"], "تم تسجيل الدخول بنجاح")
        self.assertEqual(
            login_response.data["data"]["user"]["username"],
            "unified-user",
        )

    def test_public_signup_endpoint_is_removed(self):
        response = self.client.post(
            "/api/auth/signup/",
            {
                "username": "not-created",
                "email": "not-created@example.com",
                "password": "Strong-test-password-123!",
                "password2": "Strong-test-password-123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(get_user_model().objects.filter(username="not-created").exists())

    def test_auth_validation_error_uses_the_failure_response(self):
        response = self.client.post(
            "/api/auth/login/",
            {},
            format="json",
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["status"], "FAILURE")
        self.assertEqual(response.data["code"], "request.validation_failed")
        self.assertIn("username", response.data["errors"])
        self.assertTrue(UNIFIED_RESPONSE_KEYS.issubset(response.data))


class RoleBasedAccessControlTests(APITestCase):
    def _create_user(self, username, role_code=None, superuser=False):
        User = get_user_model()
        if superuser:
            user = User.objects.create_superuser(
                username=username,
                email=f"{username}@example.com",
                password="Strong-test-password-123!",
            )
        else:
            user = User.objects.create_user(
                username=username,
                password="Strong-test-password-123!",
            )
        if role_code:
            user.profile.role = Role.objects.get(code=role_code)
            user.profile.save(update_fields=["role"])
        return user

    def _authenticate(self, user):
        _, token, _ = issue_session(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_user_without_role_cannot_read_contract_feature(self):
        self._authenticate(self._create_user("no-role-user"))

        response = self.client.get("/api/nafath-center/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_only_role_cannot_create_contract(self):
        self._authenticate(self._create_user("dean-user", "dean"))

        response = self.client.post(
            "/api/nafath-center/create",
            {"agreementNumber": "DENIED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_contract_role_can_create_contract(self):
        self._authenticate(self._create_user("contract-user", "contract"))

        response = self.client.post(
            "/api/nafath-center/create",
            {
                "agreementNumber": "ALLOWED",
                "name": "Allowed agreement",
                "companyName": "Company",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_access_control_api_is_admin_only(self):
        self._authenticate(self._create_user("ordinary-user", "contract"))
        denied = self.client.get("/api/auth/access-control/")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        admin = self._create_user("admin-user", "admin")
        self._authenticate(admin)
        allowed = self.client.get("/api/auth/access-control/")
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {role["code"] for role in allowed.data["data"]["roles"]},
            {"admin", "dean", "contract", "planning", "finance"},
        )
        self.assertNotIn("users", allowed.data["data"])

    def test_admin_can_update_role_permission(self):
        self._authenticate(self._create_user("permission-admin", "admin"))

        permission_response = self.client.patch(
            "/api/auth/access-control/",
            {
                "roleCode": "finance",
                "feature": "educational-content",
                "read": True,
                "write": True,
            },
            format="json",
        )
        self.assertEqual(permission_response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_assign_and_delete_custom_role(self):
        target = self._create_user("custom-role-user")
        self._authenticate(self._create_user("custom-role-admin", "admin"))

        created = self.client.post(
            "/api/auth/access-control/",
            {"roleCode": "auditor", "roleName": "Auditor"},
            format="json",
        )
        assigned = self.client.patch(
            f"/api/auth/users/{target.id}/",
            {"roleCode": "auditor"},
            format="json",
        )
        deleted = self.client.delete(
            "/api/auth/access-control/",
            {"roleCode": "auditor"},
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(assigned.status_code, status.HTTP_200_OK)
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        target.profile.refresh_from_db()
        self.assertIsNone(target.profile.role)

    def test_admin_manages_user_and_user_must_change_generated_password(self):
        self._authenticate(self._create_user("user-admin", "admin"))

        created = self.client.post(
            "/api/auth/users/",
            {
                "username": "managed-user",
                "email": "managed@example.com",
                "roleCode": "contract",
            },
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        temporary_password = created.data["data"]["temporaryPassword"]
        managed_user = get_user_model().objects.get(username="managed-user")
        self.assertTrue(managed_user.profile.must_change_password)
        self.assertEqual(managed_user.profile.role.code, "contract")

        self.client.credentials()
        login = self.client.post(
            "/api/auth/login/",
            {"username": "managed-user", "password": temporary_password},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertTrue(login.data["data"]["user"]["mustChangePassword"])
        token = login.data["data"]["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        denied = self.client.post(
            "/api/nafath-center/create",
            {"agreementNumber": "BEFORE-PASSWORD-CHANGE"},
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        changed = self.client.post(
            "/api/auth/change-password/",
            {
                "currentPassword": temporary_password,
                "newPassword": "New-strong-password-456!",
                "newPassword2": "New-strong-password-456!",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, status.HTTP_200_OK)
        self.assertFalse(changed.data["data"]["mustChangePassword"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {changed.data['data']['token']}")

        allowed = self.client.post(
            "/api/nafath-center/create",
            {
                "agreementNumber": "AFTER-PASSWORD-CHANGE",
                "name": "Managed agreement",
                "companyName": "Company",
            },
            format="json",
        )
        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)

    def test_admin_can_filter_update_and_deactivate_users(self):
        target = self._create_user("filter-target", "finance")
        self._authenticate(self._create_user("filter-admin", "admin"))

        filtered = self.client.get("/api/auth/users/?q=filter-target&role=finance&active=true")
        updated = self.client.patch(
            f"/api/auth/users/{target.id}/",
            {"email": "updated@example.com", "roleCode": "dean"},
            format="json",
        )
        deactivated = self.client.patch(
            f"/api/auth/users/{target.id}/",
            {"isActive": False},
            format="json",
        )

        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(filtered.data["data"]), 1)
        self.assertEqual(updated.data["data"]["user"]["role"]["code"], "dean")
        self.assertFalse(deactivated.data["data"]["user"]["isActive"])


class UnifiedRendererTests(APITestCase):
    def test_unwrapped_success_response_is_normalized(self):
        class RawResponseView(APIView):
            authentication_classes = []
            permission_classes = []

            def get(self, request):
                return Response([{"id": 1}, {"id": 2}])

        request = APIRequestFactory().get("/api/raw-test/")
        response = RawResponseView.as_view()(request)
        response.render()
        payload = json.loads(response.content)

        self.assertEqual(payload["status"], "SUCCESS")
        self.assertEqual(payload["code"], "request.success")
        self.assertEqual(payload["data"], [{"id": 1}, {"id": 2}])
        self.assertEqual(payload["totalCount"], 2)
        self.assertEqual(payload["pageSize"], 2)

    def test_unwrapped_error_response_is_normalized(self):
        class RawErrorView(APIView):
            authentication_classes = []
            permission_classes = []

            def get(self, request):
                return Response(
                    {"detail": "Missing"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        request = APIRequestFactory().get("/api/raw-error-test/")
        response = RawErrorView.as_view()(request)
        response.render()
        payload = json.loads(response.content)

        self.assertEqual(payload["status"], "FAILURE")
        self.assertEqual(payload["code"], "resource.not_found")
        self.assertIsNone(payload["data"])
        self.assertEqual(payload["errors"], {"detail": "Missing"})

# Create your tests here.
