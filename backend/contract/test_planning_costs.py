import json

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from contract.models import Role
from contract.test_helpers import authenticate_session


class PlanningCostTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='cost-editor', password='Cost-Test-249!')
        self.user.profile.role = Role.objects.get(code='contract')
        self.user.profile.save()
        authenticate_session(self.client, self.user)
        self.urls = {'nafath-centers': '/api/nafath-center/create', 'lifelong-learning': '/api/life-long/create',
                     'educational-content': '/api/educational-contents', 'other-agreements': '/api/other-agreement/create',
                     'memorandum': '/api/memorandum/create'}
        self.rows = [{'years': 'أول 5 سنوات', 'percentage': '40.00', 'details': 'حصة الجامعة'},
                     {'years': 'ثاني 3 سنوات', 'percentage': '60.00', 'details': 'حصة الجهة'}]

    def payload(self, kind, **changes):
        return {'agreementNumber': 'COST-' + kind, 'type': kind, 'name': kind, 'companyName': 'Company',
                'subject': 'تفاصيل العمل المحفوظة', 'startDate': '2026-01-01', 'endDate': '2027-01-01',
                'paymentMethod': 'table', 'costTable': self.rows, 'status': 'معتمدة', **changes}

    def test_all_five_types_save_their_own_cost_rows_and_planning_returns_them(self):
        for kind, url in self.urls.items():
            response = self.client.post(url, self.payload(kind), format='json')
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response.data['data']['costTable'], self.rows)
        response = self.client.get('/api/planning/agreements/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 5)
        for item in response.data['data']:
            self.assertEqual(item['costTable'], self.rows)
            self.assertEqual(item['paymentMethod'], 'table')
        changed = self.payload('nafath-centers', agreementNumber='COST-SECOND', costTable=[{'years': 'سنة واحدة', 'percentage': '15', 'details': 'مختلفة'}])
        self.assertEqual(self.client.post(self.urls['nafath-centers'], changed, format='json').status_code, 201)
        data = self.client.get('/api/planning/agreements/').data['data']
        original = next(item for item in data if item['agreementNumber'] == 'COST-nafath-centers')
        self.assertEqual(original['costTable'], self.rows)

    def test_multipart_table_and_plain_text_round_trip_for_every_type(self):
        for kind, url in self.urls.items():
            with self.subTest(kind=kind):
                data = self.payload(kind, costTable=json.dumps(self.rows))
                response = self.client.post(url, data, format='multipart')
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data['data']['costTable'], self.rows)
                response = self.client.post(url, self.payload(kind, agreementNumber='TEXT-' + kind,
                    paymentMethod='text', paymentText='تكلفة متفق عليها بالنص', costTable=[]), format='json')
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data['data']['paymentText'], 'تكلفة متفق عليها بالنص')
                self.assertEqual(response.data['data']['costTable'], [])

    def test_invalid_tables_return_validation_errors_without_creating_records(self):
        for value in ['broken JSON', {}, None, [], [{'years': '', 'percentage': '20'}],
                      [{'years': 'سنة', 'percentage': '-1'}], [{'years': 'سنة', 'percentage': '101'}],
                      [{'years': 'سنة', 'percentage': 'NaN'}], [{'years': 'سنة', 'percentage': '1.234'}],
                      [{'years': 'سنة'}], self.rows * 51]:
            with self.subTest(value=str(value)[:80]):
                response = self.client.post(self.urls['nafath-centers'], self.payload('nafath-centers', costTable=value), format='json')
                self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.client.get('/api/planning/agreements/').data['data'], [])

    def test_zero_percentage_is_preserved_and_hidden_records_stay_excluded(self):
        response = self.client.post(self.urls['nafath-centers'], self.payload('nafath-centers',
            costTable=[{'years': 'السنة الأولى', 'percentage': '0', 'details': ''}], isHidden=True), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['data']['costTable'][0]['percentage'], '0.00')
        self.assertEqual(self.client.get('/api/planning/agreements/').data['data'], [])

    def test_existing_dated_payment_tables_are_preserved_without_percentage_conversion(self):
        for kind in ['nafath-centers', 'lifelong-learning', 'educational-content']:
            response = self.client.post(self.urls[kind], self.payload(kind, costTable=[],
                paymentSchedule=[{'label': 'دفعة قديمة', 'amount': '250.00', 'dueDate': '2026-11-01'}]), format='json')
            self.assertEqual(response.status_code, 201, response.data)
        data = self.client.get('/api/planning/agreements/').data['data']
        self.assertEqual(len(data), 3)
        for item in data:
            self.assertEqual(item['costTable'], [])
            self.assertEqual(item['paymentSchedule'][0]['amount'], '250.00')
            self.assertEqual(item['paymentSchedule'][0]['dueDate'], '2026-11-01')

    def test_read_only_planning_user_cannot_write_cost_data(self):
        self.user.profile.role = Role.objects.get(code='planning')
        self.user.profile.save()
        for kind, url in self.urls.items():
            self.assertEqual(self.client.post(url, self.payload(kind), format='json').status_code, 403)
