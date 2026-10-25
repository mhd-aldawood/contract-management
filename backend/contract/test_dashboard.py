import io
import tempfile
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from contract.finance import DOCUMENTS
from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission


@patch('contract.dashboard.planning_today', return_value=date(2026, 10, 25))
class DashboardTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='dashboard-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(username='dashboard-user', password='test-password')
        self.client.force_authenticate(self.user)
        self.records = {}
        for kind, (model, _, filters, _) in DOCUMENTS.items():
            name_field = 'agreement_name' if kind == 'lifelong-learning' else 'name'
            hidden = kind in {'lifelong-learning', 'other-agreements'}
            start, end = (date(2026, 10, 1), date(2026, 11, 1))
            if kind in {'lifelong-learning', 'memorandum'}:
                start, end = date(2027, 1, 1), date(2027, 12, 1)
            elif kind == 'educational-content':
                start, end = date(2025, 1, 1), date(2025, 12, 1)
            record = model.objects.create(**filters, **{name_field: kind}, agreement_number=kind,
                                          start_date=start, end_date=end, is_hidden=hidden, reminder_date=date(2026, 10, 25))
            model.objects.filter(pk=record.pk).update(created_at=datetime(2026, 10, 10, tzinfo=ZoneInfo('Asia/Damascus')))
            self.records[kind] = record
        model = DOCUMENTS['nafath-centers'][0]
        self.undated = model.objects.create(name='No dates', agreement_number='UNDATED')
        model.objects.filter(pk=self.undated.pk).update(created_at=datetime(2026, 10, 10, tzinfo=ZoneInfo('Asia/Damascus')))
        for kind, removed in [('nafath-centers', False), ('nafath-centers', False), ('other-agreements', False), ('educational-content', True)]:
            order = DisbursementOrder.objects.create(**{DOCUMENTS[kind][1]: self.records[kind]},
                file=SimpleUploadedFile('order.pdf', b'order'), file_name='order.pdf', file_size=5, is_removed=removed)
            DisbursementOrder.objects.filter(pk=order.pk).update(created_at=datetime(2026, 10, 15, tzinfo=ZoneInfo('Asia/Damascus')))

    def set_role(self, code):
        self.user.profile.role = Role.objects.get(code=code)
        self.user.profile.save(update_fields=['role'])

    def get_dashboard(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200, response.data)
        return response.data['data']

    def test_admin_and_dean_have_real_aggregates_without_duplicate_agreements(self, today):
        for role in ['admin', 'dean']:
            with self.subTest(role=role):
                self.set_role(role)
                data = self.get_dashboard()
                self.assertEqual(data['mode'], role)
                self.assertEqual(data['agreements']['total'], 6)
                self.assertEqual(data['agreements']['current'], 2)
                self.assertEqual(data['agreements']['future'], 2)
                self.assertEqual(data['agreements']['finish'], 1)
                self.assertEqual(data['agreements']['hidden'], 2)
                self.assertEqual(data['finance']['orderCount'], 3)
                self.assertEqual(data['finance']['withOrders'], 2)
                self.assertEqual(data['finance']['withoutOrders'], 4)
                self.assertEqual(data['users']['total'], get_user_model().objects.count())
                self.assertEqual(len(data['charts']['monthly']), 6)
                self.assertEqual(data['charts']['monthly'][-1]['orders'], 3)
                self.assertEqual(sum(item['count'] for item in data['charts']['types']), 6)
                self.assertEqual(len(data['recentAgreements']), 5)
                self.assertEqual(len(data['recentOrders']), 3)
                self.assertEqual('roles' in data['users'], role == 'admin')
        self.assertEqual(self.client.get('/api/auth/users/').status_code, 403)

    def test_planning_never_receives_hidden_agreements_or_finance_user_statistics(self, today):
        self.set_role('planning')
        data = self.get_dashboard()
        self.assertEqual(data['scope'], 'planning-visible')
        self.assertEqual(data['agreements']['total'], 4)
        self.assertEqual(data['agreements']['hidden'], 0)
        self.assertEqual(data['agreements']['current'], 1)
        self.assertEqual(data['agreements']['future'], 1)
        self.assertIsNone(data['finance'])
        self.assertIsNone(data['users'])
        self.assertEqual(data['recentOrders'], [])
        self.assertTrue(all(not item['isHidden'] for item in data['recentAgreements']))
        self.assertTrue(all('orders' not in item for item in data['charts']['monthly']))
        self.records['nafath-centers'].is_hidden = True
        self.records['nafath-centers'].save()
        self.assertEqual(self.get_dashboard()['agreements']['total'], 3)

    def test_finance_coverage_ignores_removed_orders_and_updates_live(self, today):
        self.set_role('finance')
        data = self.get_dashboard()
        self.assertIsNone(data['users'])
        self.assertEqual(data['finance']['orderCount'], 3)
        DisbursementOrder.objects.filter(other_agreement=self.records['other-agreements']).update(is_removed=True)
        data = self.get_dashboard()
        self.assertEqual(data['finance']['orderCount'], 2)
        self.assertEqual(data['finance']['withOrders'], 1)
        self.assertEqual(data['finance']['withoutOrders'], 5)

    def test_contract_dashboard_does_not_expose_finance_or_user_metrics(self, today):
        self.set_role('contract')
        data = self.get_dashboard()
        self.assertEqual(data['agreements']['total'], 6)
        self.assertIsNone(data['finance'])
        self.assertIsNone(data['users'])
        self.assertEqual(data['agreements']['remindersDue'], 4)

    def test_custom_permissions_restrict_counts_charts_and_recent_records(self, today):
        role = Role.objects.create(code='limited-dashboard', name='Limited')
        RolePermission.objects.create(role=role, feature='home', can_read=True)
        RolePermission.objects.create(role=role, feature='memorandum', can_read=True)
        self.user.profile.role = role
        self.user.profile.save()
        data = self.get_dashboard()
        self.assertEqual(data['mode'], 'custom')
        self.assertEqual(data['agreements']['total'], 1)
        self.assertEqual([item['feature'] for item in data['charts']['types']], ['memorandum'])
        self.assertEqual([item['feature'] for item in data['recentAgreements']], ['memorandum'])
        RolePermission.objects.filter(role=role, feature='memorandum').update(can_read=False)
        data = self.get_dashboard()
        self.assertEqual(data['agreements']['total'], 0)
        self.assertEqual(data['recentAgreements'], [])

    def test_date_boundaries_and_months_use_damascus_time(self, today):
        self.set_role('contract')
        record = self.records['nafath-centers']
        record.start_date = record.end_date = date(2026, 10, 25)
        record.save()
        # 21:30 UTC on Sept 30 is already October in Damascus.
        type(record).objects.filter(pk=record.pk).update(created_at=datetime(2026, 9, 30, 21, 30, tzinfo=ZoneInfo('UTC')))
        data = self.get_dashboard()
        self.assertEqual(data['agreements']['current'], 2)
        self.assertEqual(data['charts']['monthly'][-1]['agreements'], 6)
        self.assertEqual(data['charts']['monthly'][-2]['agreements'], 0)

    def test_home_permission_password_change_and_authentication_are_enforced(self, today):
        self.set_role('finance')
        RolePermission.objects.filter(role=self.user.profile.role, feature='home').update(can_read=False)
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)
        self.set_role('admin')
        self.user.profile.must_change_password = True
        self.user.profile.save()
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 401)

    def test_query_count_does_not_grow_with_number_of_agreements(self, today):
        self.set_role('admin')
        with CaptureQueriesContext(connection) as initial:
            self.get_dashboard()
        model = DOCUMENTS['nafath-centers'][0]
        model.objects.bulk_create([model(name=f'Extra {i}', agreement_number=f'EXTRA-{i}') for i in range(50)])
        with CaptureQueriesContext(connection) as larger:
            self.get_dashboard()
        self.assertEqual(len(initial), len(larger))
        self.assertLessEqual(len(larger), 25)

    def test_test_account_seed_is_explicit_and_preserves_existing_accounts(self, today):
        output = io.StringIO()
        call_command('seed_test_users', stdout=output)
        users = get_user_model().objects.filter(username__startswith='cm_demo_')
        self.assertEqual(users.count(), 5)
        passwords = dict(users.values_list('username', 'password'))
        self.assertEqual(set(users.values_list('profile__role__code', flat=True)), {'admin', 'dean', 'finance', 'contract', 'planning'})
        self.assertFalse(users.filter(profile__must_change_password=True).exists())
        call_command('seed_test_users', stdout=io.StringIO())
        self.assertEqual(dict(users.values_list('username', 'password')), passwords)
