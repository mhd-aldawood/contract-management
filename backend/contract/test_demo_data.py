import io
import tempfile
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from rest_framework.test import APITestCase

from contract.finance import DOCUMENTS
from contract.management.commands.seed_demo_data import EXAMPLES
from contract.finance_models import DisbursementOrder
from contract.models import Role
from contract.planning import agreement_phase


class DemoDataTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='demo-seed-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.today = date(2026, 10, 25)

    def seed(self, **kwargs):
        with patch('contract.management.commands.seed_demo_data.planning_today', return_value=self.today):
            call_command('seed_demo_data', stdout=io.StringIO(), **kwargs)

    def test_creates_eight_examples_per_type_with_dates_files_and_orders(self):
        self.seed()
        for kind in EXAMPLES:
            model, _, filters, _ = DOCUMENTS[kind]
            records = model.objects.filter(agreement_number__startswith='DEMO-', **filters)
            self.assertEqual(records.count(), 8, kind)
            self.assertEqual(records.filter(is_hidden=True).count(), 2)
            self.assertEqual({agreement_phase(item.start_date, item.end_date, self.today) for item in records}, {'current', 'future', 'finish'})
            for record in records:
                self.assertTrue(record.file.storage.exists(record.file.name))
                if kind in {'other-agreements', 'memorandum'}:
                    self.assertEqual(record.rows.count(), 2)
        self.assertEqual(DisbursementOrder.objects.count(), 60)
        order = DisbursementOrder.objects.first()
        with order.file.open('rb') as uploaded:
            self.assertEqual(len(uploaded.read()), order.file_size)

    def test_rerun_preserves_edits_deleted_orders_and_existing_records(self):
        model = DOCUMENTS['nafath-centers'][0]
        original = model.objects.create(name='Existing agreement', agreement_number='REAL-1')
        self.seed()
        edited = model.objects.get(agreement_number='DEMO-NF-002')
        edited.name = 'Edited by tester'
        edited.is_hidden = True
        edited.save()
        order = edited.disbursement_orders.first()
        order.is_removed = True
        order.save()
        files = list(DisbursementOrder.objects.values_list('file', flat=True))
        self.seed()
        original.refresh_from_db()
        edited.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(original.name, 'Existing agreement')
        self.assertEqual(edited.name, 'Edited by tester')
        self.assertTrue(edited.is_hidden)
        self.assertTrue(order.is_removed)
        self.assertEqual(list(DisbursementOrder.objects.values_list('file', flat=True)), files)
        self.assertEqual(DisbursementOrder.objects.count(), 60)

    def test_dashboards_receive_role_appropriate_seeded_data(self):
        self.seed()
        user = get_user_model().objects.create_user(username='demo-dashboard-check')
        self.client.force_authenticate(user)
        for code in ['admin', 'dean', 'finance', 'contract', 'planning']:
            user.profile.role = Role.objects.get(code=code)
            user.profile.save()
            with patch('contract.dashboard.planning_today', return_value=self.today):
                response = self.client.get('/api/dashboard/')
            self.assertEqual(response.status_code, 200)
            data = response.data['data']
            self.assertEqual(data['agreements']['total'], 30 if code == 'planning' else 40)
            self.assertTrue(all(row['agreements'] > 0 for row in data['charts']['monthly']))
            self.assertEqual([item['count'] for item in data['charts']['phases']], [15, 5, 10] if code == 'planning' else [20, 10, 10])
            if code in {'admin', 'dean', 'finance'}:
                self.assertEqual(data['finance']['orderCount'], 60)
                self.assertEqual(data['finance']['withOrders'], 30)
                self.assertEqual(data['finance']['withoutOrders'], 10)

    def test_count_option_is_validated_before_writing(self):
        for count in [0, 4, 11]:
            with self.assertRaises(CommandError):
                self.seed(per_type=count)
        self.assertEqual(DisbursementOrder.objects.count(), 0)
        self.seed(per_type=5)
        self.assertEqual(DOCUMENTS['nafath-centers'][0].objects.count(), 5)
