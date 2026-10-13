import json
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView


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
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

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
        self.assertTrue(response.data["data"]["file"])
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
        self.assertTrue(UNIFIED_RESPONSE_KEYS.issubset(response.data))

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


class AuthUnifiedResponseTests(APITestCase):
    def test_signup_and_login_use_the_unified_response(self):
        signup_response = self.client.post(
            "/api/auth/signup/",
            {
                "username": "unified-user",
                "email": "unified@example.com",
                "password": "Strong-test-password-123!",
                "password2": "Strong-test-password-123!",
            },
            format="json",
            HTTP_ACCEPT_LANGUAGE="en",
        )

        self.assertEqual(signup_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(signup_response.data["status"], "SUCCESS")
        self.assertEqual(signup_response.data["code"], "auth.signup.success")
        self.assertEqual(
            set(signup_response.data),
            UNIFIED_RESPONSE_KEYS,
        )
        self.assertIn("token", signup_response.data["data"])

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
