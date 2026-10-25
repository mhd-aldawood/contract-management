from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import JSONParser

from contract.api.responses import success_response
from contract.educational_content.serializers import EducationalContentSerializer
from contract.finance import (DOCUMENTS, FinanceView, FinanceAgreementListView,
                              DisbursementOrderFileView, agreement_scope, serialize_order)
from contract.finance_models import DisbursementOrder
from contract.life_long.serializers import LifeLongAgreementSerializer
from contract.nafath_center.serializers import NafathCenterAgreementSerializer
from contract.other.serializers import AgreementSerializer


SERIALIZERS = {
    'nafath-centers': NafathCenterAgreementSerializer,
    'lifelong-learning': LifeLongAgreementSerializer,
    'educational-content': EducationalContentSerializer,
    'other-agreements': AgreementSerializer,
    'memorandum': AgreementSerializer,
}


class DeanAgreementListView(FinanceAgreementListView):
    feature_code = 'dean'


class DeanAgreementDetailView(FinanceView):
    feature_code = 'dean'

    def get(self, request, kind, pk):
        agreement, scope = agreement_scope(kind, pk)
        data = dict(SERIALIZERS[kind](agreement, context={'request': request}).data)
        orders = DisbursementOrder.objects.filter(is_removed=False, **scope).select_related('created_by', 'updated_by')
        order_data = [serialize_order(order, request, kind, pk) for order in orders]
        for order in order_data:
            order['downloadUrl'] = request.build_absolute_uri(
                f'/api/dean/agreements/{kind}/{pk}/orders/{order["id"]}/file/')
        data.update(feature=kind, category=DOCUMENTS[kind][3], key=f'{kind}-{pk}',
                    orders=order_data, orderCount=len(order_data))
        return success_response(request=request, code='request.success', data=data)


class DeanAgreementVisibilityView(FinanceView):
    feature_code = 'dean'
    parser_classes = [JSONParser]

    def patch(self, request, kind, pk):
        # This endpoint changes visibility only, never arbitrary agreement fields.
        if not isinstance(request.data, dict) or set(request.data) != {'isHidden'} or type(request.data.get('isHidden')) is not bool:
            raise ValidationError({'isHidden': ['أرسل isHidden بقيمة true أو false فقط']})
        if kind not in DOCUMENTS:
            raise NotFound()
        model, _, filters, _ = DOCUMENTS[kind]
        with transaction.atomic():
            agreement = get_object_or_404(model.objects.select_for_update(), pk=pk, **filters)
            agreement.is_hidden = request.data['isHidden']
            agreement.save(update_fields=['is_hidden', 'updated_at'])
        return success_response(request=request, code='dean.visibility.updated',
                                data={'id': pk, 'feature': kind, 'isHidden': agreement.is_hidden})


class DeanOrderFileView(DisbursementOrderFileView):
    feature_code = 'dean'
