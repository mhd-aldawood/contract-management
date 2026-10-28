import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from contract.doctoral_models import DoctoralContract
from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission
from contract.test_helpers import authenticate_session, grant_headers, close_download


class DoctoralContractTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='doctoral-contract-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable(); self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(username='doctoral-editor', password='Doctoral-Test-472!')
        self.set_role('contract')
        authenticate_session(self.client, self.user)
        self.payload = {'contractNumber': 'PHD-001', 'doctorName': 'الدكتور أحمد', 'tasks': 'الإشراف والتدريس',
                        'doctorRank': 'أستاذ مساعد', 'duration': 'سنة دراسية واحدة', 'commencementOrder': 'أمر المباشرة رقم 12'}

    def set_role(self, role):
        self.user.profile.role = Role.objects.get(code=role)
        self.user.profile.save()

    def create(self, **changes):
        response = self.client.post('/api/doctoral-contracts/', {**self.payload, **changes}, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['data']

    def test_six_fields_are_persisted_listed_and_retrieved(self):
        data = self.create()
        for key, value in self.payload.items():
            self.assertEqual(data[key], value)
        self.assertEqual(data['name'], self.payload['doctorName'])
        self.assertEqual(data['agreementNumber'], 'PHD-001')
        self.assertFalse(data['hasFile'])
        listed = self.client.get('/api/doctoral-contracts/')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data['totalCount'], 1)
        self.assertEqual(self.client.get(f"/api/doctoral-contracts/{data['id']}/").data['data']['tasks'], self.payload['tasks'])

    def test_file_is_private_and_download_uses_the_existing_grant_protocol(self):
        data = self.create(file=SimpleUploadedFile('وثيقة.txt', b'doctoral contract document'))
        self.assertTrue(data['hasFile'])
        self.assertEqual(data['fileName'], 'وثيقة.txt')
        self.assertNotIn('file', data)
        self.assertNotIn('/media/', str(data))
        headers = grant_headers(self.client, 'doctoral-contracts', data['id'])
        response = self.client.get('/api/files/download/', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'doctoral contract document')
        close_download(response)
        self.assertEqual(self.client.get('/api/files/download/', **headers).status_code, 409)

    def test_required_fields_duplicates_and_invalid_documents_return_400(self):
        for key in self.payload:
            response = self.client.post('/api/doctoral-contracts/', {**self.payload, key: ' '}, format='json')
            self.assertEqual(response.status_code, 400, response.data)
        self.create()
        duplicate = self.client.post('/api/doctoral-contracts/', self.payload, format='json')
        self.assertEqual(duplicate.status_code, 400)
        for name, content in [('bad.html', b'bad'), ('empty.pdf', b'')]:
            response = self.client.post('/api/doctoral-contracts/', {**self.payload, 'contractNumber': 'OTHER',
                'file': SimpleUploadedFile(name, content)}, format='multipart')
            self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(DoctoralContract.objects.count(), 1)

    def test_each_role_is_guarded_and_download_is_separate_from_read(self):
        data = self.create(file=SimpleUploadedFile('doc.txt', b'document'))
        for role in ['admin', 'dean', 'finance', 'planning']:
            self.set_role(role)
            self.assertEqual(self.client.get('/api/doctoral-contracts/').status_code, 200)
            if role != 'admin':
                self.assertEqual(self.client.post('/api/doctoral-contracts/', self.payload, format='json').status_code, 403)
                self.assertEqual(self.client.patch(f"/api/doctoral-contracts/{data['id']}/", {'tasks': 'changed'}, format='json').status_code, 403)
        RolePermission.objects.filter(role__code='planning', feature='doctoral-contracts').update(can_download=False)
        response = self.client.post('/api/files/grants/', {'kind': 'doctoral-contracts', 'agreementId': data['id']}, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/doctoral-contracts/').status_code, 401)

    def test_planning_dean_and_dashboard_include_contract_and_respect_hiding(self):
        data = self.create(isHidden=True)
        self.assertEqual(self.client.get('/api/planning/agreements/').data['data'], [])
        self.set_role('dean')
        detail = self.client.get(f"/api/dean/agreements/doctoral-contracts/{data['id']}/")
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertEqual(detail.data['data']['doctorRank'], 'أستاذ مساعد')
        self.assertEqual(self.client.get('/api/dashboard/').data['data']['agreements']['total'], 1)
        shown = self.client.patch(f"/api/dean/agreements/doctoral-contracts/{data['id']}/visibility/", {'isHidden': False}, format='json')
        self.assertEqual(shown.status_code, 200)
        self.set_role('planning')
        planning = self.client.get('/api/planning/agreements/').data['data']
        self.assertEqual(planning[0]['feature'], 'doctoral-contracts')
        self.assertEqual(planning[0]['duration'], 'سنة دراسية واحدة')

    def test_finance_orders_are_scoped_to_the_doctoral_contract(self):
        data = self.create()
        self.set_role('finance')
        url = f"/api/finance/agreements/doctoral-contracts/{data['id']}/orders/"
        uploaded = self.client.post(url, {'files': [SimpleUploadedFile('order.txt', b'doctoral order')]}, format='multipart')
        self.assertEqual(uploaded.status_code, 201, uploaded.data)
        order = DisbursementOrder.objects.get()
        self.assertEqual(order.doctoral_contract_id, data['id'])
        self.assertEqual(self.client.get('/api/finance/agreements/').data['data'][0]['orderCount'], 1)
        self.assertEqual(self.client.get('/api/doctoral-contracts/', {'hasOrders': 'true'}).data['totalCount'], 1)

    def test_update_preserves_file_until_replaced_and_duplicate_number_is_rejected(self):
        first = self.create(file=SimpleUploadedFile('first.txt', b'first'))
        self.create(contractNumber='PHD-002')
        url = f"/api/doctoral-contracts/{first['id']}/"
        response = self.client.patch(url, {'tasks': 'مهام محدثة'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['data']['hasFile'])
        self.assertEqual(response.data['data']['tasks'], 'مهام محدثة')
        self.assertEqual(self.client.patch(url, {'contractNumber': 'PHD-002'}, format='json').status_code, 400)
        self.assertEqual(self.client.get('/api/doctoral-contracts/999999/').status_code, 404)
