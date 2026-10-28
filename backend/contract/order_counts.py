from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError


def with_order_counts(queryset, request=None):
    queryset = queryset.annotate(order_count=Count(
        'disbursement_orders', filter=Q(disbursement_orders__is_removed=False), distinct=True))
    value = request.query_params.get('hasOrders', '') if request else ''
    if value not in {'', 'true', 'false'}:
        raise ValidationError({'hasOrders': ['استخدم true أو false لتصفية أوامر الصرف']})
    if value == 'true':
        return queryset.filter(order_count__gt=0)
    if value == 'false':
        return queryset.filter(order_count=0)
    return queryset


class AgreementOrderCountMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in ['file', 'fileUrl', 'storedName']:
            data.pop(key, None)
        data['hasFile'] = bool(instance.file)
        return data

    def get_orderCount(self, instance):
        count = getattr(instance, 'order_count', None)
        return count if count is not None else instance.disbursement_orders.filter(is_removed=False).count()
