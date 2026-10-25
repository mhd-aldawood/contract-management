import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from contract.finance import DOCUMENTS
from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission


class DeanReviewTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='dean-review-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(username='dean-review', password='test-password')
        self.set_role('dean')
        self.client.force_authenticate(self.user)
        self.records = {}
        for kind, (model, _, filters, _) in DOCUMENTS.items():
            name_field = 'agreement_name' if kind == 'lifelong-learning' else 'name'
            self.records[kind] = model.objects.create(
                **filters, **{name_field: kind}, agreement_number=kind,
                start_date=date(2026, 10, 1), end_date=date(2027, 10, 1),
                is_hidden=True,
            )

    def set_role(self, code):
        self.user.profile.role = Role.objects.get(code=code)
        self.user.profile.save(update_fields=['role'])

    def url(self, kind='nafath-centers'):
        return f'/api/dean/agreements/{kind}/{self.records[kind].pk}/'

    def create_order(self, kind='nafath-centers', removed=False):
        relation = DOCUMENTS[kind][1]
        return DisbursementOrder.objects.create(
            **{relation: self.records[kind]},
            file=SimpleUploadedFile('order.pdf', b'%PDF test dean order', content_type='application/pdf'),
            file_name='order.pdf', file_size=20, title='أمر صرف', notes='ملاحظات المالية',
            created_by=self.user, updated_by=self.user, is_removed=removed,
        )

    def test_all_hidden_document_types_and_full_details_are_available(self):
        self.create_order()
        self.create_order(removed=True)
        response = self.client.get('/api/dean/agreements/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['totalCount'], 5)
        self.assertEqual({item['feature'] for item in response.data['data']}, set(DOCUMENTS))
        self.assertTrue(all(item['isHidden'] for item in response.data['data']))
        for kind in DOCUMENTS:
            with self.subTest(kind=kind):
                response = self.client.get(self.url(kind))
                self.assertEqual(response.status_code, 200, response.data)
                data = response.data['data']
                self.assertEqual(data['name'], kind)
                self.assertEqual(data['startDate'], '2026-10-01')
                self.assertTrue(data['isHidden'])
                self.assertEqual(data['orderCount'], 1 if kind == 'nafath-centers' else 0)
                if data['orders']:
                    self.assertEqual(data['orders'][0]['notes'], 'ملاحظات المالية')
                    self.assertIn('/api/dean/', data['orders'][0]['downloadUrl'])

    def test_visibility_persists_and_controls_planning_for_every_type(self):
        self.assertEqual(self.client.get('/api/planning/agreements/').data['data'], [])
        for kind, record in self.records.items():
            with self.subTest(kind=kind):
                url = self.url(kind) + 'visibility/'
                response = self.client.patch(url, {'isHidden': False}, format='json')
                self.assertEqual(response.status_code, 200, response.data)
                record.refresh_from_db()
                self.assertFalse(record.is_hidden)
                planning = self.client.get('/api/planning/agreements/').data['data']
                self.assertEqual([item['key'] for item in planning], [f'{kind}-{record.pk}'])
                self.assertEqual(self.client.patch(url, {'isHidden': True}, format='json').status_code, 200)
                self.assertEqual(self.client.get('/api/planning/agreements/').data['data'], [])

    def test_dean_download_is_independent_of_finance_access_and_scoped_to_document(self):
        RolePermission.objects.filter(role=self.user.profile.role, feature='finance').update(can_read=False, can_write=False)
        order = self.create_order()
        url = self.url() + f'orders/{order.pk}/file/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF test dean order')
        response.close()
        self.assertEqual(self.client.get(self.url('memorandum') + f'orders/{order.pk}/file/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/finance/agreements/nafath-centers/{self.records["nafath-centers"].pk}/orders/').status_code, 403)
        order.is_removed = True
        order.save(update_fields=['is_removed'])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_read_only_dean_can_review_but_cannot_change_visibility(self):
        RolePermission.objects.filter(role=self.user.profile.role, feature='dean').update(can_write=False)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.assertEqual(self.client.patch(self.url() + 'visibility/', {'isHidden': False}, format='json').status_code, 403)
        self.records['nafath-centers'].refresh_from_db()
        self.assertTrue(self.records['nafath-centers'].is_hidden)

    def test_other_roles_and_unauthenticated_users_are_denied(self):
        for role in ['contract', 'planning', 'finance']:
            self.set_role(role)
            self.assertEqual(self.client.get('/api/dean/agreements/').status_code, 403)
            self.assertEqual(self.client.get(self.url()).status_code, 403)
            self.assertEqual(self.client.patch(self.url() + 'visibility/', {'isHidden': False}, format='json').status_code, 403)
        self.set_role('admin')
        self.assertEqual(self.client.get('/api/dean/agreements/').status_code, 200)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/dean/agreements/').status_code, 401)

    def test_visibility_endpoint_rejects_other_fields_and_non_boolean_values(self):
        for payload in [{}, {'isHidden': 'false'}, {'isHidden': 0}, {'isHidden': None},
                        {'isHidden': False, 'name': 'changed'}, [{'isHidden': False}]]:
            with self.subTest(payload=payload):
                response = self.client.patch(self.url() + 'visibility/', payload, format='json')
                self.assertEqual(response.status_code, 400, response.data)
        record = self.records['nafath-centers']
        record.refresh_from_db()
        self.assertTrue(record.is_hidden)
        self.assertEqual(record.name, 'nafath-centers')

    def test_wrong_type_and_missing_document_do_not_expose_or_modify_agreements(self):
        record = self.records['memorandum']
        wrong = f'/api/dean/agreements/other-agreements/{record.pk}/'
        for url in [wrong, '/api/dean/agreements/missing/1/', '/api/dean/agreements/nafath-centers/999999/']:
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.patch(url + 'visibility/', {'isHidden': False}, format='json').status_code, 404)
        record.refresh_from_db()
        self.assertTrue(record.is_hidden)
