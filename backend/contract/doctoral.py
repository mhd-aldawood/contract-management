from pathlib import Path

from django.db import transaction
from rest_framework import serializers
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView

from contract.api.responses import success_response
from contract.doctoral_models import DoctoralContract
from contract.finance import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from contract.order_counts import AgreementOrderCountMixin, with_order_counts
from contract.rbac import HasFeaturePermission


class DoctoralContractSerializer(AgreementOrderCountMixin, serializers.ModelSerializer):
    contractNumber = serializers.CharField(source='agreement_number', max_length=100)
    agreementNumber = serializers.CharField(source='agreement_number', read_only=True)
    doctorName = serializers.CharField(source='name', max_length=255)
    name = serializers.CharField(read_only=True)
    tasks = serializers.CharField(source='subject', max_length=10000)
    subject = serializers.CharField(read_only=True)
    doctorRank = serializers.CharField(source='doctor_rank', max_length=150)
    duration = serializers.CharField(max_length=255)
    commencementOrder = serializers.CharField(source='commencement_order', max_length=2000)
    startDate = serializers.DateField(source='start_date', read_only=True)
    endDate = serializers.DateField(source='end_date', read_only=True)
    reminderDate = serializers.DateField(source='reminder_date', read_only=True)
    fileName = serializers.CharField(source='file_name', read_only=True)
    isHidden = serializers.BooleanField(source='is_hidden', required=False)
    file = serializers.FileField(required=False, allow_null=True, write_only=True)
    orderCount = serializers.SerializerMethodField()
    costTable = serializers.SerializerMethodField()

    class Meta:
        model = DoctoralContract
        fields = ['id', 'type', 'contractNumber', 'agreementNumber', 'doctorName', 'name', 'tasks', 'subject',
                  'doctorRank', 'duration', 'commencementOrder', 'startDate', 'endDate', 'reminderDate', 'fileName', 'file', 'isHidden', 'orderCount', 'costTable']
        read_only_fields = ['id', 'type']

    def get_costTable(self, instance):
        return []

    def validate_contractNumber(self, value):
        queryset = DoctoralContract.objects.filter(agreement_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('رقم العقد موجود مسبقاً.')
        return value

    def validate_file(self, value):
        if value and (not value.size or value.size > MAX_UPLOAD_BYTES or Path(value.name).suffix.lower() not in ALLOWED_EXTENSIONS):
            raise serializers.ValidationError('أرفق وثيقة غير فارغة بصيغة PDF أو Word أو صورة أو TXT أو Excel، بحجم لا يتجاوز 19 ميغابايت.')
        return value

    def create(self, validated_data):
        file = validated_data.get('file')
        if file:
            validated_data['file_name'] = file.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        previous_name, storage = instance.file.name, instance.file.storage
        if 'file' in validated_data:
            file = validated_data['file']
            validated_data['file_name'] = file.name if file else ''
        instance = super().update(instance, validated_data)
        if 'file' in validated_data and previous_name and previous_name != instance.file.name:
            transaction.on_commit(lambda: storage.delete(previous_name), robust=True)
        return instance


class DoctoralContractListCreateView(ListCreateAPIView):
    serializer_class = DoctoralContractSerializer
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    feature_code = 'doctoral-contracts'

    def get_queryset(self):
        return with_order_counts(DoctoralContract.objects.all(), self.request)

    def list(self, request, *args, **kwargs):
        data = self.get_serializer(self.get_queryset(), many=True).data
        return success_response(request=request, code='request.success', data=data, total_count=len(data), page_size=len(data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(request=request, code='doctoral.created', data=serializer.data, status_code=201)


class DoctoralContractDetailView(RetrieveUpdateAPIView):
    queryset = DoctoralContract.objects.all()
    serializer_class = DoctoralContractSerializer
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    feature_code = 'doctoral-contracts'

    def retrieve(self, request, *args, **kwargs):
        return success_response(request=request, code='request.success', data=self.get_serializer(self.get_object()).data)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(request=request, code='doctoral.updated', data=serializer.data)
