from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db.models import Count, F, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.finance import DOCUMENTS
from contract.finance_models import DisbursementOrder
from contract.models import Role, RolePermission
from contract.planning import planning_today
from contract.rbac import HasFeaturePermission, is_admin_user


DAMASCUS = ZoneInfo('Asia/Damascus')
PHASES = [('current', 'حالية'), ('future', 'مستقبلية'), ('finish', 'منتهية')]


def month_start(day, offset=0):
    index = day.year * 12 + day.month - 1 + offset
    return datetime(index // 12, index % 12 + 1, 1, tzinfo=DAMASCUS)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'home'

    def get(self, request):
        user = request.user
        admin = is_admin_user(user)
        role = user.profile.role
        role_code = 'admin' if admin else role.code if role else ''
        readable = set(DOCUMENTS) | {'dean', 'finance', 'planning'} if admin else set(
            RolePermission.objects.filter(role=role, can_read=True).values_list('feature', flat=True))
        mode = role_code if role_code in {'admin', 'dean', 'finance', 'contract', 'planning'} else 'custom'
        planning_only = mode == 'planning'
        # Dashboard access never grants access to another feature's records.
        broad_access = not planning_only and bool({'dean', 'finance'} & readable)
        include_finance = broad_access
        today = planning_today()
        first_month = month_start(today, -5)
        this_month = month_start(today)
        next_month = month_start(today, 1)
        valid_dates = Q(start_date__isnull=False, end_date__isnull=False, start_date__lte=F('end_date'))
        phases = {
            'current': valid_dates & Q(start_date__lte=today, end_date__gte=today),
            'future': valid_dates & Q(start_date__gt=today),
            'finish': valid_dates & Q(end_date__lt=today),
        }
        totals = dict.fromkeys(['total', 'current', 'future', 'finish', 'newThisMonth', 'hidden', 'visible',
                                'remindersDue', 'expiringSoon'], 0)
        types, recent = [], []
        monthly = {month_start(today, offset).strftime('%Y-%m'): {
            'month': month_start(today, offset).strftime('%Y-%m'), 'agreements': 0,
            **({'orders': 0} if include_finance else {}),
        } for offset in range(-5, 1)}
        finance = dict.fromkeys(['orderCount', 'ordersThisMonth', 'withOrders', 'withoutOrders'], 0) if include_finance else None
        order_scope = Q(pk__in=[])

        for kind, (model, relation, filters, label) in DOCUMENTS.items():
            if planning_only:
                if 'planning' not in readable:
                    continue
                queryset = model.objects.filter(is_hidden=False, **filters)
            elif broad_access or kind in readable:
                queryset = model.objects.filter(**filters)
            elif 'planning' in readable:
                queryset = model.objects.filter(is_hidden=False, **filters)
            else:
                continue
            aggregates = {
                'total': Count('pk', distinct=True),
                **{key: Count('pk', filter=condition, distinct=True) for key, condition in phases.items()},
                'newThisMonth': Count('pk', filter=Q(created_at__gte=this_month, created_at__lt=next_month), distinct=True),
                'hidden': Count('pk', filter=Q(is_hidden=True), distinct=True),
                'visible': Count('pk', filter=Q(is_hidden=False), distinct=True),
                'remindersDue': Count('pk', filter=Q(reminder_date__lte=today) & ~phases['finish'], distinct=True),
                'expiringSoon': Count('pk', filter=valid_dates & Q(end_date__gte=today, end_date__lte=today + timedelta(days=30)), distinct=True),
            }
            if include_finance:
                active = Q(disbursement_orders__is_removed=False)
                aggregates.update(
                    orderCount=Count('disbursement_orders', filter=active, distinct=True),
                    ordersThisMonth=Count('disbursement_orders', filter=active & Q(disbursement_orders__created_at__gte=this_month, disbursement_orders__created_at__lt=next_month), distinct=True),
                    withOrders=Count('pk', filter=active, distinct=True),
                )
                order_scope |= Q(**{f'{relation}__in': queryset.values('pk')})
            stats = queryset.aggregate(**aggregates)
            for key in totals:
                totals[key] += stats[key]
            if include_finance:
                for key in ['orderCount', 'ordersThisMonth', 'withOrders']:
                    finance[key] += stats[key]
            types.append({'feature': kind, 'label': label, 'count': stats['total'],
                          **({'orderCount': stats['orderCount']} if include_finance else {})})
            for row in queryset.filter(created_at__gte=first_month, created_at__lt=next_month).order_by().annotate(
                    month=TruncMonth('created_at', tzinfo=DAMASCUS)).values('month').annotate(count=Count('pk')):
                monthly[row['month'].strftime('%Y-%m')]['agreements'] += row['count']
            name_field = 'agreement_name' if kind == 'lifelong-learning' else 'name'
            for record in queryset.order_by('-updated_at', '-pk').values(
                    'id', name_field, 'agreement_number', 'start_date', 'end_date', 'reminder_date', 'updated_at', 'is_hidden')[:5]:
                recent.append({'id': record['id'], 'key': f'{kind}-{record["id"]}', 'feature': kind, 'category': label,
                               'name': record[name_field], 'agreementNumber': record['agreement_number'],
                               'startDate': record['start_date'], 'endDate': record['end_date'],
                               'reminderDate': record['reminder_date'], 'updatedAt': record['updated_at'], 'isHidden': record['is_hidden']})

        recent.sort(key=lambda record: (record['updatedAt'], record['key']), reverse=True)
        recent_orders = []
        if include_finance:
            finance['withoutOrders'] = totals['total'] - finance['withOrders']
            orders = DisbursementOrder.objects.filter(order_scope, is_removed=False)
            for row in orders.filter(created_at__gte=first_month, created_at__lt=next_month).order_by().annotate(
                    month=TruncMonth('created_at', tzinfo=DAMASCUS)).values('month').annotate(count=Count('pk')):
                monthly[row['month'].strftime('%Y-%m')]['orders'] = row['count']
            for order in orders.select_related('nafath_agreement', 'lifelong_agreement', 'educational_agreement', 'other_agreement', 'doctoral_contract')[:5]:
                for kind, (_, relation, filters, label) in DOCUMENTS.items():
                    agreement = getattr(order, relation)
                    if agreement is None or any(getattr(agreement, key) != value for key, value in filters.items()):
                        continue
                    recent_orders.append({'id': order.pk, 'title': order.title or order.file_name,
                                          'agreementName': agreement.agreement_name if kind == 'lifelong-learning' else agreement.name,
                                          'agreementKey': f'{kind}-{agreement.pk}', 'createdAt': order.created_at})
                    break

        users = None
        if admin or 'dean' in readable:
            users = get_user_model().objects.aggregate(total=Count('pk'), active=Count('pk', filter=Q(is_active=True)),
                                                       inactive=Count('pk', filter=Q(is_active=False)))
            if admin:
                users['roles'] = Role.objects.count()
        return success_response(request=request, code='request.success', data={
            'mode': mode, 'today': today, 'generatedAt': timezone.now(),
            'scope': 'planning-visible' if planning_only else 'all' if broad_access else 'permitted-features',
            'agreements': totals, 'users': users, 'finance': finance,
            'charts': {'phases': [{'code': code, 'label': label, 'count': totals[code]} for code, label in PHASES],
                       'types': types, 'monthly': list(monthly.values())},
            'recentAgreements': recent[:5], 'recentOrders': recent_orders,
        })
