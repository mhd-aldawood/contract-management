import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission
from contract.nafath_center.models import NafathCenterAgreement
from contract.other.models import Agreement


class FinanceOrderTests(APITestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='finance-orders-test-')
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user(username='finance-user', password='test-password')
        self.set_role('finance')
        self.client.force_authenticate(self.user)
        self.agreement = NafathCenterAgreement.objects.create(name='Agreement', agreement_number='FN-1', company_name='Company', subject='Agreement details', is_hidden=True)
        self.url = f'/api/finance/agreements/nafath-centers/{self.agreement.pk}/orders/'

    def set_role(self, code):
        self.user.profile.role = Role.objects.get(code=code)
        self.user.profile.save(update_fields=['role'])

    def file(self, name='order.pdf', content=b'%PDF-1.4 test order'):
        return SimpleUploadedFile(name, content, content_type='application/pdf')

    def upload(self, files=None, url=None):
        return self.client.post(url or self.url, {'files': files or [self.file()]}, format='multipart')

    def test_multiple_orders_are_persisted_and_counted_for_hidden_agreement(self):
        response = self.upload([self.file('first.pdf'), self.file('second.pdf')])
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data['data']), 2)
        listed = self.client.get(self.url)
        self.assertEqual(listed.data['totalCount'], 2)
        self.assertEqual({order['fileName'] for order in listed.data['data']}, {'first.pdf', 'second.pdf'})
        finance = self.client.get('/api/finance/agreements/')
        self.assertEqual(finance.status_code, 200)
        self.assertEqual(finance.data['data'][0]['orderCount'], 2)
        self.assertEqual(finance.data['data'][0]['name'], 'Agreement')
        self.assertEqual(finance.data['data'][0]['details'], 'Agreement details')

    def test_reupload_replaces_only_the_selected_order(self):
        created = self.upload([self.file('first.pdf'), self.file('second.pdf')])
        order_id = created.data['data'][0]['id']
        original = DisbursementOrder.objects.get(pk=order_id)
        original_name = original.file.name
        storage = original.file.storage
        with self.captureOnCommitCallbacks(execute=True):
            updated = self.client.patch(f'{self.url}{order_id}/', {'file': self.file('replacement.pdf', b'replacement content')}, format='multipart')
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data['data']['id'], order_id)
        self.assertEqual(updated.data['data']['fileName'], 'replacement.pdf')
        self.assertFalse(storage.exists(original_name))
        self.assertEqual(DisbursementOrder.objects.filter(is_removed=False).count(), 2)
        downloaded = self.client.get(f'{self.url}{order_id}/file/')
        self.assertEqual(b''.join(downloaded.streaming_content), b'replacement content')
        self.assertIn('attachment;', downloaded['Content-Disposition'])
        downloaded.close()

    def test_remove_affects_only_one_order_and_blocks_its_download(self):
        created = self.upload([self.file('first.pdf'), self.file('second.pdf')])
        order_id = created.data['data'][0]['id']
        removed = self.client.delete(f'{self.url}{order_id}/')
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(self.client.get(self.url).data['totalCount'], 1)
        self.assertEqual(self.client.get('/api/finance/agreements/').data['data'][0]['orderCount'], 1)
        self.assertEqual(self.client.get(f'{self.url}{order_id}/file/').status_code, 404)
        self.assertTrue(DisbursementOrder.objects.get(pk=order_id).is_removed)
        self.assertEqual(self.client.delete(f'{self.url}{order_id}/').status_code, 404)

    def test_order_cannot_be_accessed_or_modified_through_another_agreement(self):
        created = self.upload()
        order_id = created.data['data'][0]['id']
        other = NafathCenterAgreement.objects.create(name='Another', agreement_number='FN-2', company_name='Company')
        other_url = f'/api/finance/agreements/nafath-centers/{other.pk}/orders/{order_id}/'
        self.assertEqual(self.client.get(f'{other_url}file/').status_code, 404)
        self.assertEqual(self.client.patch(other_url, {'file': self.file()}, format='multipart').status_code, 404)
        self.assertEqual(self.client.delete(other_url).status_code, 404)

    def test_every_document_type_has_its_own_orders(self):
        from contract.educational_content.models import EducationalContent
        from contract.life_long.models import LifeLongAgreement
        for kind, model, name_field in [
            ('lifelong-learning', LifeLongAgreement, 'agreement_name'),
            ('educational-content', EducationalContent, 'name'),
            ('other-agreements', Agreement, 'name'),
            ('memorandum', Agreement, 'name'),
        ]:
            with self.subTest(kind=kind):
                record = model.objects.create(type=kind if kind in {'memorandum', 'other-agreements'} else 'life-long' if kind == 'lifelong-learning' else 'educational-content',
                                              agreement_number=kind, **{name_field: kind},
                                              start_date=date(2026, 10, 1), end_date=date(2027, 10, 1))
                url = f'/api/finance/agreements/{kind}/{record.pk}/orders/'
                self.assertEqual(self.upload(url=url).status_code, 201)
                self.assertEqual(self.client.get(url).data['totalCount'], 1)
        items = self.client.get('/api/finance/agreements/').data['data']
        self.assertEqual(len(items), 5)
        self.assertEqual({item['feature'] for item in items}, {'nafath-centers', 'lifelong-learning', 'educational-content', 'other-agreements', 'memorandum'})

    def test_read_only_role_can_download_but_cannot_change_files(self):
        order_id = self.upload().data['data'][0]['id']
        self.set_role('dean')
        self.assertEqual(self.client.get(self.url).status_code, 200)
        response = self.client.get(f'{self.url}{order_id}/file/')
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.upload().status_code, 403)
        self.assertEqual(self.client.patch(f'{self.url}{order_id}/', {'file': self.file()}, format='multipart').status_code, 403)
        self.assertEqual(self.client.delete(f'{self.url}{order_id}/').status_code, 403)
        self.assertEqual(self.client.patch(f'{self.url}{order_id}/', {'title': 'Denied edit'}, format='json').status_code, 403)

    def test_modify_metadata_preserves_file_and_order_count(self):
        order_id = self.upload().data['data'][0]['id']
        original_name = DisbursementOrder.objects.get(pk=order_id).file.name
        updated = self.client.patch(f'{self.url}{order_id}/', {'title': 'أمر الصرف الأول', 'notes': 'ملاحظات المالية'}, format='json')
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data['data']['title'], 'أمر الصرف الأول')
        self.assertEqual(updated.data['data']['notes'], 'ملاحظات المالية')
        self.assertEqual(DisbursementOrder.objects.get(pk=order_id).file.name, original_name)
        self.assertEqual(self.client.get(self.url).data['totalCount'], 1)
        with self.captureOnCommitCallbacks(execute=True):
            replaced = self.client.patch(f'{self.url}{order_id}/', {'file': self.file('new.pdf')}, format='multipart')
        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(replaced.data['data']['title'], 'أمر الصرف الأول')
        self.assertEqual(replaced.data['data']['notes'], 'ملاحظات المالية')

    def test_invalid_metadata_does_not_change_order(self):
        order_id = self.upload().data['data'][0]['id']
        for payload in [{}, {'title': ' '}, {'notes': 'x' * 2001}]:
            self.assertEqual(self.client.patch(f'{self.url}{order_id}/', payload, format='json').status_code, 400)
        self.assertEqual(self.client.get(self.url).data['totalCount'], 1)

    def test_finance_permission_is_required_and_admin_can_configure_it(self):
        order_id = self.upload().data['data'][0]['id']
        self.set_role('contract')
        self.assertEqual(self.client.get('/api/finance/agreements/').status_code, 403)
        self.assertEqual(self.client.get(f'{self.url}{order_id}/file/').status_code, 403)
        permission = RolePermission.objects.get(role=self.user.profile.role, feature='finance')
        permission.can_read = True
        permission.save(update_fields=['can_read'])
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.upload().status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'{self.url}{order_id}/file/').status_code, 401)

    def test_invalid_file_batch_creates_no_orders(self):
        response = self.upload([self.file('valid.pdf'), self.file('invalid.html')])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(DisbursementOrder.objects.count(), 0)
        self.assertEqual(self.client.post(self.url, {}, format='multipart').status_code, 400)
        self.assertEqual(self.upload([self.file('empty.pdf', b'')]).status_code, 400)
        self.assertEqual(self.upload([self.file(f'{i}.pdf') for i in range(21)]).status_code, 400)

    def test_memo_and_other_agreement_do_not_share_access_paths(self):
        record = Agreement.objects.create(type='memorandum', agreement_number='MEMO', name='Memo', start_date=date(2026, 10, 1), end_date=date(2027, 10, 1))
        wrong_url = f'/api/finance/agreements/other-agreements/{record.pk}/orders/'
        self.assertEqual(self.client.get(wrong_url).status_code, 404)
        self.assertEqual(self.upload(url=wrong_url).status_code, 404)
