from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from contract.models import Role, RolePermission
from contract.request_models import ContractRequest, BidMinute
from contract.test_helpers import authenticate_session


class ContractRequestTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='request-editor', password='Request-Test-923!')
        self.set_role('contract')
        authenticate_session(self.client, self.user)
        self.payload = {'justificationMemo': 'مذكرة تبريرية لاختبار العقد', 'technicalSpecs': 'دفتر شروط فني',
            'legalSpecs': 'دفتر شروط حقوقي', 'announceStart': '2026-10-01', 'announceEnd': '2026-10-15',
            'reminderDate': '2026-10-10', 'status': 'success',
            'bids': [{'number': 'M-001', 'date': '2026-10-03', 'subject': 'فض العروض الأول'},
                     {'number': 'M-002', 'date': '2026-10-04', 'subject': 'فض العروض الثاني'}],
            'wishes': ['الرغبة الأولى', 'الرغبة الثانية']}

    def set_role(self, code):
        self.user.profile.role = Role.objects.get(code=code)
        self.user.profile.save()

    def create(self, **changes):
        response = self.client.post('/api/contract-requests/', {**self.payload, **changes}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['data']

    def test_create_list_and_details_preserve_all_fields_including_reminder(self):
        data = self.create()
        for key, value in self.payload.items():
            self.assertEqual(data[key], value)
        self.assertEqual(ContractRequest.objects.count(), 1)
        self.assertEqual(BidMinute.objects.count(), 2)
        listed = self.client.get('/api/contract-requests/')
        self.assertEqual(listed.data['totalCount'], 1)
        detail = self.client.get(f"/api/contract-requests/{data['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data['data']['reminderDate'], '2026-10-10')

    def test_failed_status_saves_without_announcement_dates_and_discards_dependent_rows(self):
        data = self.create(status='failed', announceStart='not a date', announceEnd=None,
                           bids=[{'invalid': 'ignored'}], wishes=['ignored'])
        self.assertIsNone(data['announceStart'])
        self.assertIsNone(data['announceEnd'])
        self.assertEqual(data['bids'], [])
        self.assertEqual(data['wishes'], [])
        self.assertEqual(data['reminderDate'], '2026-10-10')
        self.assertEqual(BidMinute.objects.count(), 0)

    def test_success_requires_valid_dates_and_partially_filled_minutes_are_rejected(self):
        for changes in [{'announceStart': None}, {'announceEnd': None}, {'announceEnd': '2026-09-01'},
                        {'bids': [{'number': 'Partial'}]}, {'status': 'unknown'}, {'reminderDate': None}]:
            with self.subTest(changes=changes):
                response = self.client.post('/api/contract-requests/', {**self.payload, **changes}, format='json')
                self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(ContractRequest.objects.count(), 0)

    def test_invalid_or_missing_fields_return_controlled_validation_errors(self):
        for key in ['justificationMemo', 'technicalSpecs', 'legalSpecs']:
            self.assertEqual(self.client.post('/api/contract-requests/', {**self.payload, key: ' '}, format='json').status_code, 400)
        for data in [[], {'arbitrary': True}, {**self.payload, 'is_deleted': True}, {**self.payload, 'wishes': ['']},
                     {**self.payload, 'wishes': ['x'] * 101}, {**self.payload, 'bids': self.payload['bids'] * 51}]:
            self.assertEqual(self.client.post('/api/contract-requests/', data, format='json').status_code, 400)

    def test_update_replaces_ordered_rows_and_failed_transition_clears_saved_rows(self):
        data = self.create()
        url = f"/api/contract-requests/{data['id']}/"
        response = self.client.patch(url, {'bids': [self.payload['bids'][1]], 'wishes': ['محدثة']}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['data']['bids'][0]['number'], 'M-002')
        self.assertEqual(BidMinute.objects.count(), 1)
        response = self.client.patch(url, {'status': 'failed'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['data']['bids'], [])
        self.assertEqual(response.data['data']['wishes'], [])
        self.assertIsNone(response.data['data']['announceStart'])
        self.assertEqual(BidMinute.objects.count(), 0)
        self.assertEqual(self.client.patch(url, {'status': 'success'}, format='json').status_code, 400)

    def test_optional_tables_can_be_empty_and_same_day_announcements_are_allowed(self):
        data = self.create(announceEnd='2026-10-01', bids=[], wishes=[])
        self.assertEqual(data['bids'], [])
        self.assertEqual(data['announceStart'], data['announceEnd'])

    def test_search_and_status_filter_do_not_duplicate_rows(self):
        first = self.create()
        self.create(status='failed', justificationMemo='طلب فاشل')
        for query in ['M-001', 'فض العروض', 'تبريرية']:
            response = self.client.get('/api/contract-requests/', {'q': query, 'status': 'success'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual([row['id'] for row in response.data['data']], [first['id']])
        self.assertEqual(self.client.get('/api/contract-requests/', {'status': 'failed'}).data['totalCount'], 1)
        self.assertEqual(self.client.get('/api/contract-requests/', {'status': 'bad'}).status_code, 400)

    def test_delete_removes_from_list_and_blocks_read_update_and_repeat_delete(self):
        data = self.create()
        url = f"/api/contract-requests/{data['id']}/"
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertTrue(ContractRequest.objects.get(pk=data['id']).is_deleted)
        self.assertEqual(self.client.get('/api/contract-requests/').data['data'], [])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.patch(url, {'status': 'failed'}, format='json').status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)

    def test_role_permissions_guard_every_mutation_and_no_role_is_denied(self):
        data = self.create()
        url = f"/api/contract-requests/{data['id']}/"
        for code in ['dean', 'planning', 'finance']:
            self.set_role(code)
            self.assertEqual(self.client.get('/api/contract-requests/').status_code, 200)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.post('/api/contract-requests/', self.payload, format='json').status_code, 403)
            self.assertEqual(self.client.patch(url, {'status': 'failed'}, format='json').status_code, 403)
            self.assertEqual(self.client.delete(url).status_code, 403)
        self.set_role('admin')
        self.assertEqual(self.client.patch(url, {'technicalSpecs': 'Updated'}, format='json').status_code, 200)
        self.set_role('contract')
        RolePermission.objects.filter(role=self.user.profile.role, feature='contract-requests').update(can_read=False, can_write=False)
        self.assertEqual(self.client.get('/api/contract-requests/').status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/contract-requests/').status_code, 401)

    def test_query_count_stays_constant_as_records_and_minutes_increase(self):
        self.create()
        with CaptureQueriesContext(connection) as first:
            self.client.get('/api/contract-requests/')
        for index in range(5):
            self.create(justificationMemo=f'مذكرة {index}')
        with CaptureQueriesContext(connection) as later:
            self.client.get('/api/contract-requests/')
        self.assertEqual(len(first), len(later))
