import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from contract.finance import DOCUMENTS
from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission
from contract.test_helpers import authenticate_session, grant_headers, close_download


LIST_URLS = {'nafath-centers': '/api/nafath-center/', 'lifelong-learning': '/api/life-long/',
             'educational-content': '/api/educational-contents', 'other-agreements': '/api/other-agreement/',
             'memorandum': '/api/memorandum/'}


class AgreementOrdersTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='agreement-order-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(username='contract-order-reader', password='test-password')
        self.set_role('contract')
        authenticate_session(self.client, self.user)
        self.records = {}
        self.empty = {}
        for kind in DOCUMENTS:
            self.records[kind] = self.agreement(kind, 'with')
            self.empty[kind] = self.agreement(kind, 'empty')
            self.order(kind)
            self.order(kind)
            self.order(kind, removed=True)

    def set_role(self, code):
        self.user.profile.role = Role.objects.get(code=code)
        self.user.profile.save(update_fields=['role'])

    def agreement(self, kind, suffix, hidden=False):
        model, _, filters, _ = DOCUMENTS[kind]
        name_field = 'agreement_name' if kind == 'lifelong-learning' else 'name'
        return model.objects.create(**filters, **{name_field: kind + suffix}, agreement_number=kind + suffix,
                                    start_date=date(2026, 1, 1), end_date=date(2027, 1, 1), is_hidden=hidden)

    def order(self, kind, removed=False, record=None):
        return DisbursementOrder.objects.create(**{DOCUMENTS[kind][1]: record or self.records[kind]},
            file=SimpleUploadedFile('order.txt', b'test order'), file_name='order.txt', file_size=10,
            title='Test order', notes='Finance notes', created_by=self.user, updated_by=self.user, is_removed=removed)

    def url(self, kind='nafath-centers', record=None):
        return f'/api/agreement-orders/{kind}/{(record or self.records[kind]).pk}/'

    def test_all_lists_include_active_counts_and_support_both_filters(self):
        for kind, url in LIST_URLS.items():
            with self.subTest(kind=kind):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual({item['id']: item['orderCount'] for item in response.data['data']},
                                 {self.records[kind].pk: 2, self.empty[kind].pk: 0})
                self.assertEqual([item['id'] for item in self.client.get(url, {'hasOrders': 'true'}).data['data']], [self.records[kind].pk])
                self.assertEqual([item['id'] for item in self.client.get(url, {'hasOrders': 'false'}).data['data']], [self.empty[kind].pk])
                self.assertEqual(self.client.get(url, {'hasOrders': 'invalid'}).status_code, 400)

    def test_agreement_read_allows_only_related_active_orders_and_downloads(self):
        self.assertEqual(self.client.get('/api/finance/agreements/').status_code, 403)
        for kind in DOCUMENTS:
            with self.subTest(kind=kind):
                response = self.client.get(self.url(kind))
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data['totalCount'], 2)
                self.assertEqual(len(response.data['data']), 2)
                order = response.data['data'][0]
                self.assertIn('/api/agreement-orders/', order['downloadUrl'])
                downloaded = self.client.get(order['downloadUrl'], **grant_headers(self.client, kind, self.records[kind].pk, order['id']))
                self.assertEqual(downloaded.status_code, 200)
                self.assertEqual(b''.join(downloaded.streaming_content), b'test order')
                self.assertEqual(downloaded['Cache-Control'], 'private, no-store')
                close_download(downloaded)
                self.assertEqual(self.client.get(self.url(kind, self.empty[kind])).data['data'], [])
                self.assertEqual(self.client.post(self.url(kind), {}, format='json').status_code, 405)
                self.assertEqual(self.client.delete(self.url(kind)).status_code, 405)

    def test_planning_counts_filters_and_downloads_respect_hidden_records(self):
        hidden = self.agreement('nafath-centers', 'hidden', hidden=True)
        hidden_order = self.order('nafath-centers', record=hidden)
        self.set_role('planning')
        data = self.client.get('/api/planning/agreements/', {'hasOrders': 'true'}).data['data']
        self.assertEqual(len(data), len(DOCUMENTS))
        self.assertTrue(all(item['orderCount'] == 2 and not item['isHidden'] for item in data))
        self.assertEqual(len(self.client.get('/api/planning/agreements/', {'hasOrders': 'false'}).data['data']), len(DOCUMENTS))
        self.assertEqual(self.client.get('/api/planning/agreements/', {'hasOrders': 'invalid'}).status_code, 400)
        for role in ['planning', 'admin']:
            self.set_role(role)
            self.assertEqual(self.client.get(self.url(), {'scope': 'planning'}).status_code, 200)
            self.assertEqual(self.client.get(self.url(record=hidden), {'scope': 'planning'}).status_code, 404)
            self.assertEqual(self.client.get(self.url(record=hidden) + f'{hidden_order.pk}/file/', {'scope': 'planning'}).status_code, 404)

    def test_custom_permissions_and_mandatory_password_change_are_enforced(self):
        role = Role.objects.create(code='one-agreement-reader', name='One agreement reader')
        RolePermission.objects.create(role=role, feature='nafath-centers', can_read=True)
        self.user.profile.role = role
        self.user.profile.save()
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.assertEqual(self.client.get(self.url('memorandum')).status_code, 403)
        self.assertEqual(self.client.get(self.url(), {'scope': 'planning'}).status_code, 403)
        self.assertEqual(self.client.get(self.url(), {'scope': 'dean'}).status_code, 403)
        self.assertEqual(self.client.get(self.url(), {'scope': 'finance'}).status_code, 403)
        RolePermission.objects.create(role=role, feature='planning', can_read=True)
        self.assertEqual(self.client.get(self.url('memorandum'), {'scope': 'planning'}).status_code, 200)
        self.user.profile.must_change_password = True
        self.user.profile.save()
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url()).status_code, 401)

    def test_order_and_document_scope_cannot_be_swapped(self):
        order = self.records['nafath-centers'].disbursement_orders.filter(is_removed=False).first()
        self.assertEqual(self.client.get(self.url('memorandum') + f'{order.pk}/file/').status_code, 404)
        memo = self.records['memorandum']
        self.assertEqual(self.client.get(f'/api/agreement-orders/other-agreements/{memo.pk}/').status_code, 404)
        self.assertEqual(self.client.get('/api/agreement-orders/invalid/1/').status_code, 404)
        self.assertEqual(self.client.get(self.url(), {'scope': 'invalid'}).status_code, 400)
        order.is_removed = True
        order.save()
        self.assertEqual(self.client.get(self.url() + f'{order.pk}/file/').status_code, 404)
        data = self.client.get(LIST_URLS['nafath-centers'], {'hasOrders': 'true'}).data['data']
        self.assertEqual(data[0]['orderCount'], 1)

    def test_finance_and_dean_filters_share_counts_without_expanding_write_access(self):
        for role, prefix in [('finance', 'finance'), ('dean', 'dean')]:
            self.set_role(role)
            response = self.client.get(f'/api/{prefix}/agreements/', {'hasOrders': 'true'})
            self.assertEqual(len(response.data['data']), len(DOCUMENTS))
            self.assertTrue(all(item['orderCount'] == 2 for item in response.data['data']))
            self.assertEqual(len(self.client.get(f'/api/{prefix}/agreements/', {'hasOrders': 'false'}).data['data']), len(DOCUMENTS))
            RolePermission.objects.filter(role=self.user.profile.role, feature='nafath-centers').update(can_read=False)
            self.assertEqual(self.client.get(self.url(), {'scope': prefix}).status_code, 200)
            self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_count_queries_do_not_grow_per_row_and_detail_count_stays_correct(self):
        self.set_role('admin')
        url = LIST_URLS['nafath-centers']
        with CaptureQueriesContext(connection) as before:
            self.client.get(url)
        for i in range(10):
            self.agreement('nafath-centers', str(i))
        with CaptureQueriesContext(connection) as after:
            self.client.get(url)
        self.assertEqual(len(before), len(after))
        response = self.client.get(f'/api/educational-contents/{self.records["educational-content"].pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['orderCount'], 2)
