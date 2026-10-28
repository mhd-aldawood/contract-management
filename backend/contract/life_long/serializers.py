import json
from rest_framework import serializers
from contract.costs import CostTableField, AgreementCostMixin
from contract.order_counts import AgreementOrderCountMixin

from contract.life_long.models import LifeLongAgreementPaymentRow, LifeLongAgreement

class FlexibleDateField(serializers.DateField):
    def to_internal_value(self, value):
        if value in ('', None):
            return None
        return super().to_internal_value(value)


class PaymentScheduleRowSerializer(serializers.ModelSerializer):
    dueDate = serializers.DateField(
        source='due_date', required=False, allow_null=True
    )

    class Meta:
        model = LifeLongAgreementPaymentRow
        # NOTE: field names here = wire names (camelCase)
        fields = ['id', 'label', 'amount', 'dueDate', 'order']
        read_only_fields = ['id']

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر')
        return value


class LifeLongAgreementSerializer(AgreementCostMixin, AgreementOrderCountMixin, serializers.ModelSerializer):
    orderCount = serializers.SerializerMethodField()
    costTable = CostTableField(source='cost_table', required=False)
    # ---- nested rows: wire key "paymentSchedule" → model attr "payment_schedule"
    paymentSchedule  = PaymentScheduleRowSerializer(
        source='payment_schedule',
        many=True,
        required=False,
        allow_null=True,
    )

    # ---- camelCase wire names → snake_case model attrs
    agreementNumber   = serializers.CharField(source='agreement_number',   required=False, allow_blank=True)
    companyName       = serializers.CharField(source='company_name',       required=False, allow_blank=True)
    name              = serializers.CharField(source='agreement_name', required=False, allow_blank=True)
    startDate         = serializers.DateField(source='start_date',   required=False, allow_null=True)
    endDate           = serializers.DateField(source='end_date',     required=False, allow_null=True)
    reminderDate      = FlexibleDateField(source='reminder_date', required=False, allow_null=True)
    paymentMethod     = serializers.CharField(source='payment_method', required=False, allow_blank=True)
    paymentText       = serializers.CharField(source='payment_text',   required=False, allow_blank=True)
    budgetType        = serializers.CharField(source='budget_type',    required=False, allow_blank=True)
    isHidden          = serializers.BooleanField(source='is_hidden',   required=False)
    fileName          = serializers.CharField(source='file_name',      required=False, allow_blank=True)

    class Meta:
        model = LifeLongAgreement
        # list every wire field you want exposed
        fields = [
            'orderCount', 'costTable',
             'id', 'type', 'agreementNumber', 'name', 'companyName',
             'startDate', 'endDate', 'reminderDate', 'subject',
            'paymentMethod', 'paymentText', 'paymentSchedule',
            'status', 'disbursement', 'budgetType',
            'isHidden', 'fileName', 'file',
        ]
        read_only_fields = ['id']

    # ------------------------------------------------------------------
    # Handle BOTH JSON and multipart/form-data clients
    # ------------------------------------------------------------------
    def to_internal_value(self, data):
        # 1. QueryDict (multipart / urlencoded) -> plain dict
        if hasattr(data, 'dict'):
            data = data.dict()

        # 3. If the client sent the list as a JSON string, decode it
        raw = data.get('paymentSchedule')
        if isinstance(raw, str):
            try:
                data['paymentSchedule'] = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                raise serializers.ValidationError({
                    'paymentSchedule': 'صيغة جدول الدفعات غير صالحة'
                })

        # 4. Boolean-ish string coercion for multipart ("true"/"false")
        if isinstance(data.get('isHidden'), str):
            data['isHidden'] = data['isHidden'].lower() in ('1', 'true', 'yes', 'on')

        return super().to_internal_value(data)

    def create(self, validated_data):
        rows = validated_data.pop('payment_schedule', None) or []
        agreement = LifeLongAgreement.objects.create(**validated_data)
        self._save_rows(agreement, rows)
        return agreement

    def update(self, instance, validated_data):
        rows = validated_data.pop('payment_schedule', None)
        instance = super().update(instance, validated_data)
        if rows is not None:
            instance.payment_schedule.all().delete()
            self._save_rows(instance, rows)
        return instance

    @staticmethod
    def _save_rows(agreement, rows):
        LifeLongAgreementPaymentRow.objects.bulk_create([
            LifeLongAgreementPaymentRow(
                agreement=agreement,
                label=row.get('label') or '',
                amount=row['amount'],
                due_date=row.get('due_date'),
                order=i,
            )
            for i, row in enumerate(rows)
        ])
