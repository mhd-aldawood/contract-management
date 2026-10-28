"""Agreement-specific percentage allocations, separate from dated payment schedules."""
import json
from decimal import Decimal

from rest_framework import serializers


class CostRowSerializer(serializers.Serializer):
    years = serializers.CharField(max_length=120)
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'))
    details = serializers.CharField(max_length=2000, allow_blank=True, required=False, default='')


class CostTableField(serializers.Field):
    def to_internal_value(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError('صيغة جدول التكلفة غير صالحة.')
        if not isinstance(value, list) or len(value) > 100:
            raise serializers.ValidationError('أدخل جدول تكلفة لا يتجاوز 100 صف.')
        serializer = CostRowSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return [{**row, 'percentage': str(row['percentage'])} for row in serializer.validated_data]

    def to_representation(self, value):
        return value


class AgreementCostMixin:
    def validate(self, attrs):
        attrs = super().validate(attrs)
        method = attrs.get('payment_method', getattr(self.instance, 'payment_method', ''))
        if 'cost_table' in attrs and method == 'table' and not attrs['cost_table'] and not attrs.get('payment_schedule'):
            raise serializers.ValidationError({'costTable': ['أضف صف تكلفة واحداً على الأقل.']})
        return attrs
