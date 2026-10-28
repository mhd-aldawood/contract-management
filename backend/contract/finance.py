from pathlib import Path

from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.educational_content.models import EducationalContent
from contract.doctoral_models import DoctoralContract
from contract.finance_models import DisbursementOrder
from contract.life_long.models import LifeLongAgreement
from contract.nafath_center.models import NafathCenterAgreement
from contract.other.models import Agreement
from contract.order_counts import with_order_counts
from contract.rbac import HasFeaturePermission


DOCUMENTS = {
    'doctoral-contracts': (DoctoralContract, 'doctoral_contract', {}, 'عقود الدكتوراه'),
    'nafath-centers': (NafathCenterAgreement, 'nafath_agreement', {}, 'اتفاقيات مراكز النفاذ'),
    'lifelong-learning': (LifeLongAgreement, 'lifelong_agreement', {}, 'التعلم مدى الحياة'),
    'educational-content': (EducationalContent, 'educational_agreement', {}, 'المحتوى التعليمي'),
    'other-agreements': (Agreement, 'other_agreement', {'type': 'other-agreements'}, 'اتفاقيات أخرى'),
    'memorandum': (Agreement, 'other_agreement', {'type': 'memorandum'}, 'مذكرات التفاهم'),
}
MAX_UPLOAD_BYTES = 19 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx', '.xls', '.xlsx', '.txt'}


def agreement_scope(kind, pk):
    if kind not in DOCUMENTS:
        raise NotFound()
    model, relation, filters, _ = DOCUMENTS[kind]
    agreement = get_object_or_404(model, pk=pk, **filters)
    return agreement, {relation: agreement}


def validate_files(files):
    if not files:
        raise ValidationError({'files': ['اختر ملف أمر صرف واحداً على الأقل']})
    if len(files) > 20 or sum(file.size for file in files) > MAX_UPLOAD_BYTES:
        raise ValidationError({'files': ['الحد الأقصى 20 ملفاً بحجم إجمالي 19 ميغابايت']})
    for file in files:
        serializers.FileField(max_length=512).run_validation(file)
        if Path(file.name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValidationError({'files': ['الصيغ المسموحة: PDF، صور، Word، Excel، TXT']})


def serialize_order(order, request, kind, pk):
    return {
        'id': order.pk, 'fileName': order.file_name, 'fileSize': order.file_size,
        'title': order.title or order.file_name, 'notes': order.notes,
        'createdAt': order.created_at, 'updatedAt': order.updated_at,
        'uploadedBy': order.created_by.username if order.created_by else '',
        'updatedBy': order.updated_by.username if order.updated_by else '',
        'downloadUrl': reverse('finance-order-file', kwargs={'kind': kind, 'pk': pk, 'order_id': order.pk}, request=request),
    }


class FinanceView(APIView):
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'finance'


class FinanceAgreementListView(FinanceView):
    def get(self, request):
        data = []
        for kind, (model, _, filters, category) in DOCUMENTS.items():
            agreements = with_order_counts(model.objects.filter(**filters), request)
            if kind in {'other-agreements', 'memorandum'}:
                agreements = agreements.prefetch_related('rows')
            # Hide affects Planning only; Finance can upload orders for any agreement.
            for agreement in agreements:
                details = getattr(agreement, 'subject', '')
                if kind in {'other-agreements', 'memorandum'}:
                    details = ' — '.join(f'{row.header}: {row.body}' for row in list(agreement.rows.all())[:2])
                data.append({
                    'id': agreement.pk, 'feature': kind, 'key': f'{kind}-{agreement.pk}',
                    'name': agreement.agreement_name if kind == 'lifelong-learning' else agreement.name,
                    'agreementNumber': agreement.agreement_number, 'category': category,
                    'orderCount': agreement.order_count,
                    'details': details[:500],
                    'isHidden': agreement.is_hidden,
                    'startDate': agreement.start_date,
                    'endDate': agreement.end_date,
                    'reminderDate': agreement.reminder_date,
                })
        return success_response(request=request, code='request.success', data=data,
                                total_count=len(data), page_size=len(data))


class DisbursementOrderListView(FinanceView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, kind, pk):
        _, scope = agreement_scope(kind, pk)
        orders = DisbursementOrder.objects.filter(is_removed=False, **scope).select_related('created_by', 'updated_by')
        data = [serialize_order(order, request, kind, pk) for order in orders]
        return success_response(request=request, code='request.success', data=data,
                                total_count=len(data), page_size=len(data))

    def post(self, request, kind, pk):
        _, scope = agreement_scope(kind, pk)
        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        validate_files(files)
        orders = []
        try:
            with transaction.atomic():
                for file in files:
                    order = DisbursementOrder(**scope, file=file, file_name=file.name,
                                              file_size=file.size, created_by=request.user, updated_by=request.user)
                    orders.append(order)
                    order.save()
        except Exception:
            # Rollback does not remove uploaded storage objects automatically.
            for order in orders:
                if order.file and order.file._committed:
                    order.file.delete(save=False)
            raise
        return success_response(request=request, code='finance.orders.uploaded', status_code=201,
                                data=[serialize_order(order, request, kind, pk) for order in orders],
                                total_count=len(orders), page_size=len(orders))


class DisbursementOrderDetailView(FinanceView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def patch(self, request, kind, pk, order_id):
        _, scope = agreement_scope(kind, pk)
        class OrderUpdateSerializer(serializers.Serializer):
            title = serializers.CharField(required=False, max_length=255)
            notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
            file = serializers.FileField(required=False)

        serializer = OrderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        changes = serializer.validated_data
        if not changes:
            raise ValidationError({'detail': ['أدخل اسماً أو ملاحظات أو اختر ملفاً للاستبدال']})
        files = request.FILES.getlist('file')
        if len(files) > 1:
            raise ValidationError({'file': ['اختر ملفاً واحداً للاستبدال']})
        file = changes.get('file')
        if file:
            validate_files([file])
        order = None
        try:
            with transaction.atomic():
                order = get_object_or_404(DisbursementOrder.objects.select_for_update(), pk=order_id, is_removed=False, **scope)
                storage, previous_name = order.file.storage, order.file.name
                fields = ['title', 'notes', 'updated_by', 'updated_at']
                if file:
                    if not order.title or order.title == order.file_name:
                        order.title = file.name
                    order.file = file
                    order.file_name = file.name
                    order.file_size = file.size
                    fields.extend(['file', 'file_name', 'file_size'])
                for field in ['title', 'notes']:
                    if field in changes:
                        setattr(order, field, changes[field])
                order.updated_by = request.user
                order.save(update_fields=fields)
                if file:
                    transaction.on_commit(lambda: storage.delete(previous_name), robust=True)
        except Exception:
            if file and order and order.file and order.file._committed and order.file.name != previous_name:
                order.file.delete(save=False)
            raise
        return success_response(request=request, code='finance.order.replaced' if file else 'finance.order.updated', data=serialize_order(order, request, kind, pk))

    def delete(self, request, kind, pk, order_id):
        _, scope = agreement_scope(kind, pk)
        with transaction.atomic():
            order = get_object_or_404(DisbursementOrder.objects.select_for_update(), pk=order_id, is_removed=False, **scope)
            order.is_removed = True
            order.updated_by = request.user
            order.save(update_fields=['is_removed', 'updated_by', 'updated_at'])
        return success_response(request=request, code='finance.order.removed')


class DisbursementOrderFileView(FinanceView):
    def get(self, request, kind, pk, order_id):
        _, scope = agreement_scope(kind, pk)
        get_object_or_404(DisbursementOrder, pk=order_id, is_removed=False, **scope)
        from contract.file_access import consume_download_grant
        return consume_download_grant(request, kind=kind, pk=pk, order_id=order_id)
