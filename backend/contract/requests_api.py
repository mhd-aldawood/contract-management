from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from contract.api.responses import success_response
from contract.rbac import HasFeaturePermission
from contract.request_models import ContractRequest, BidMinute


class BidMinuteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidMinute
        fields = ['number', 'date', 'subject']


class ContractRequestSerializer(serializers.ModelSerializer):
    justificationMemo = serializers.CharField(source='justification_memo', max_length=20000)
    technicalSpecs = serializers.CharField(source='technical_specs', max_length=2000)
    legalSpecs = serializers.CharField(source='legal_specs', max_length=2000)
    announceStart = serializers.DateField(source='announce_start', required=False, allow_null=True)
    announceEnd = serializers.DateField(source='announce_end', required=False, allow_null=True)
    reminderDate = serializers.DateField(source='reminder_date')
    bids = BidMinuteSerializer(many=True, required=False)
    wishes = serializers.ListField(child=serializers.CharField(max_length=2000), max_length=100, required=False)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = ContractRequest
        fields = ['id', 'justificationMemo', 'technicalSpecs', 'legalSpecs', 'announceStart', 'announceEnd',
                  'reminderDate', 'status', 'bids', 'wishes', 'createdAt', 'updatedAt']
        read_only_fields = ['id']

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'detail': ['أرسل كائن JSON صحيحاً.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: ['حقل غير معروف.'] for key in unknown})
        data = dict(data)
        state = data.get('status', getattr(self.instance, 'status', None))
        if state == 'failed':
            data.update(announceStart=None, announceEnd=None, bids=[], wishes=[])
        return super().to_internal_value(data)

    def validate_bids(self, rows):
        if len(rows) > 100:
            raise serializers.ValidationError('الحد الأقصى 100 محضر.')
        return rows

    def validate(self, attrs):
        state = attrs.get('status', getattr(self.instance, 'status', None))
        start = attrs.get('announce_start', getattr(self.instance, 'announce_start', None))
        end = attrs.get('announce_end', getattr(self.instance, 'announce_end', None))
        errors = {}
        if state == 'success':
            if not start:
                errors['announceStart'] = ['تاريخ بداية الإعلان مطلوب.']
            if not end:
                errors['announceEnd'] = ['تاريخ نهاية الإعلان مطلوب.']
            if start and end and end < start:
                errors['announceEnd'] = ['تاريخ نهاية الإعلان يجب ألا يسبق بدايته.']
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        bids = validated_data.pop('bids', [])
        record = ContractRequest.objects.create(**validated_data)
        self.save_bids(record, bids)
        return record

    @transaction.atomic
    def update(self, instance, validated_data):
        bids = validated_data.pop('bids', None)
        instance = ContractRequest.objects.select_for_update().get(pk=instance.pk, is_deleted=False)
        instance = super().update(instance, validated_data)
        if bids is not None:
            instance.bids.all().delete()
            self.save_bids(instance, bids)
        return instance

    @staticmethod
    def save_bids(record, rows):
        BidMinute.objects.bulk_create([BidMinute(contract_request=record, order=index, **row) for index, row in enumerate(rows)])


class ContractRequestListCreateView(ListCreateAPIView):
    serializer_class = ContractRequestSerializer
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'contract-requests'

    def get_queryset(self):
        queryset = ContractRequest.objects.filter(is_deleted=False).prefetch_related('bids')
        state = self.request.query_params.get('status', '')
        if state not in {'', 'success', 'failed'}:
            raise ValidationError({'status': ['الحالة غير صالحة.']})
        if state:
            queryset = queryset.filter(status=state)
        query = self.request.query_params.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(justification_memo__icontains=query) | Q(technical_specs__icontains=query) |
                Q(legal_specs__icontains=query) | Q(bids__number__icontains=query) | Q(bids__subject__icontains=query)).distinct()
        return queryset

    def list(self, request, *args, **kwargs):
        data = self.get_serializer(self.get_queryset(), many=True).data
        return success_response(request=request, code='request.success', data=data, total_count=len(data), page_size=len(data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(request=request, code='contract_request.created', data=serializer.data, status_code=201)


class ContractRequestDetailView(RetrieveUpdateDestroyAPIView):
    queryset = ContractRequest.objects.filter(is_deleted=False).prefetch_related('bids')
    serializer_class = ContractRequestSerializer
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'contract-requests'

    def retrieve(self, request, *args, **kwargs):
        return success_response(request=request, code='request.success', data=self.get_serializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(request=request, code='contract_request.updated', data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        record.is_deleted = True
        record.save(update_fields=['is_deleted', 'updated_at'])
        return success_response(request=request, code='contract_request.deleted')
