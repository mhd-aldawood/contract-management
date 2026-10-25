from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from contract.finance import DOCUMENTS
from contract.finance_models import DisbursementOrder
from contract.models import Profile
from contract.planning import planning_today


EXAMPLES = {
    'nafath-centers': ('NF', 'اتفاقية مركز نفاذ', 'nafath-center'),
    'lifelong-learning': ('LL', 'اتفاقية تعلم مدى الحياة', 'life-long'),
    'educational-content': ('EC', 'اتفاقية محتوى تعليمي', 'educational-content'),
    'other-agreements': ('OT', 'اتفاقية تعاون', 'other-agreements'),
    'memorandum': ('MO', 'مذكرة تفاهم', 'memorandum'),
}
CITIES = ['دمشق', 'حلب', 'حمص', 'اللاذقية', 'طرطوس', 'حماة', 'السويداء', 'درعا', 'دير الزور', 'الحسكة']
DATE_RANGES = [(-90, 90), (-30, 14), (-45, 30), (15, 120), (60, 240), (-300, -120), (-180, -7), (-7, 365), (30, 180), (-60, 60)]
DAMASCUS = ZoneInfo('Asia/Damascus')


class Command(BaseCommand):
    help = 'Explicitly seed clearly marked demo agreements and Finance files. Existing records are never overwritten.'

    def add_arguments(self, parser):
        parser.add_argument('--per-type', type=int, default=8, help='Number of examples per agreement type (5–10).')

    def handle(self, *args, **options):
        count = options['per_type']
        if not 5 <= count <= 10:
            raise CommandError('--per-type must be between 5 and 10.')
        today = planning_today()
        uploader = Profile.objects.filter(user__username='cm_demo_finance', role__code='finance').select_related('user').first()
        uploader = uploader.user if uploader else None
        created_count = order_count = skipped_count = 0
        for kind, (model, relation, _, _) in DOCUMENTS.items():
            code, label, wire_type = EXAMPLES[kind]
            type_index = list(EXAMPLES).index(kind)
            # Vary hidden examples by type so Planning retains data in every month.
            hidden_indexes = {[2, 1, 7, 0, 2][type_index], [4, 3, 4, 3, 4][type_index]}
            for index in range(count):
                number = f'DEMO-{code}-{index + 1:03d}'
                if model.objects.filter(agreement_number=number).exists():
                    skipped_count += 1
                    continue
                start_offset, end_offset = DATE_RANGES[index]
                start, end = today + timedelta(days=start_offset), today + timedelta(days=end_offset)
                amount = Decimal((index + 1) * 250000)
                name_field = 'agreement_name' if kind == 'lifelong-learning' else 'name'
                values = {
                    'agreement_number': number, 'type': wire_type,
                    name_field: f'تجريبي — {label} {CITIES[index]}',
                    'start_date': start, 'end_date': end,
                    'reminder_date': end - timedelta(days=14) if end < today else today + timedelta(days=(-2 if index in {1, 2} else 7 + index)),
                    'is_hidden': index in hidden_indexes,
                }
                if kind not in {'other-agreements', 'memorandum'}:
                    values.update(company_name=f'جهة تجريبية في {CITIES[index]}',
                                  subject=f'سجل تجريبي لاختبار {label} في لوحة التحكم.',
                                  payment_method='table' if index % 2 else 'text',
                                  payment_text='' if index % 2 else 'تسدد القيمة وفق الشروط المتفق عليها — بيانات تجريبية.',
                                  status='منتهية' if end < today else 'مستقبلية' if start > today else 'حالية',
                                  budget_type='investment' if index % 2 else 'current',
                                  disbursement='بيانات تجريبية لا تمثل صرفاً فعلياً')
                if kind in {'nafath-centers', 'educational-content'}:
                    values['estimated_cost'] = amount
                if kind == 'educational-content':
                    values.update(additional_courses='مهارات رقمية وتطوير محتوى', quarterly_due=amount / 4,
                                  contract_text='نص عقد تجريبي مخصص لاختبار العرض والتصفية والصلاحيات.')
                # Spread creation over six months so monthly charts contain useful data.
                month_index = today.year * 12 + today.month - 1 - index % 6
                created_at = min(datetime(month_index // 12, month_index % 12 + 1, min(today.day, 5), 10, tzinfo=DAMASCUS), timezone.now())
                # Historical records appear consistently in the recent-activity table.
                updated_at = max(created_at, timezone.now() - timedelta(minutes=index))
                stored_files = []
                try:
                    with transaction.atomic():
                        agreement = model.objects.create(**values)
                        attachment_name = f'{number}-agreement.txt'
                        agreement.file.save(attachment_name, ContentFile(
                            f'{values[name_field]}\nرقم الاتفاقية: {number}\nمرفق تجريبي لاختبار النظام.\n'.encode('utf-8')), save=False)
                        stored_files.append((agreement.file.storage, agreement.file.name))
                        if kind == 'educational-content':
                            agreement.original_name = attachment_name
                            agreement.stored_name = agreement.file.name.rsplit('/', 1)[-1]
                        else:
                            agreement.file_name = attachment_name
                        agreement.save()
                        model.objects.filter(pk=agreement.pk).update(created_at=created_at, updated_at=updated_at)
                        if kind in {'other-agreements', 'memorandum'}:
                            agreement.rows.create(order=0, header='موضوع الاتفاقية', body=f'تعاون تجريبي مع جهة في {CITIES[index]}.')
                            agreement.rows.create(order=1, header='التزامات الطرفين', body='بنود تجريبية لمراجعة الاتفاقية واختبار صلاحيات الأدوار.')
                        elif index % 2:
                            for payment_index in range(2):
                                agreement.payment_schedule.create(label=f'الدفعة {payment_index + 1}', amount=amount / 2,
                                                                  due_date=start + timedelta(days=30 * payment_index), order=payment_index)
                        # Include agreements with zero, one, two and three Finance orders.
                        for order_index in range(index % 4):
                            filename = f'{number}-order-{order_index + 1}.txt'
                            content = f'أمر صرف تجريبي {order_index + 1}\n{number}\nملف للاختبار فقط، لا يمثل عملية دفع.\n'.encode('utf-8')
                            order = DisbursementOrder(**{relation: agreement}, file_name=filename, file_size=len(content),
                                                      title=f'أمر صرف تجريبي {order_index + 1} — {CITIES[index]}',
                                                      notes='مرفق تجريبي لاختبار التنزيل والاستبدال والحذف.', created_by=uploader, updated_by=uploader)
                            order.file.save(filename, ContentFile(content), save=False)
                            stored_files.append((order.file.storage, order.file.name))
                            order.save()
                            DisbursementOrder.objects.filter(pk=order.pk).update(created_at=created_at, updated_at=updated_at)
                        created_count += 1
                        order_count += index % 4
                except Exception:
                    # Database rollback does not automatically remove storage objects.
                    for storage, name in stored_files:
                        storage.delete(name)
                    raise
            self.stdout.write(f'{kind}: {count} demo slots ready; existing examples preserved.')
        self.stdout.write(self.style.SUCCESS(
            f'Created {created_count} agreements and {order_count} Finance orders; skipped {skipped_count} existing examples.'))
