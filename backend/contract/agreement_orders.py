from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.finance import DOCUMENTS, agreement_scope, serialize_order
from contract.finance_models import DisbursementOrder
from contract.rbac import user_has_feature_permission


class CanReadAgreementOrders(BasePermission):
    def has_permission(self, request, view):
        kind = view.kwargs.get('kind')
        if kind not in DOCUMENTS:
            raise NotFound()
        scope = request.query_params.get('scope', 'agreement')
        if scope not in {'agreement', 'planning', 'dean', 'finance'}:
            raise ValidationError({'scope': ['النطاق غير صالح']})
        feature = kind if scope == 'agreement' else scope
        return user_has_feature_permission(request.user, feature, 'read')


class AgreementOrderReadView(APIView):
    permission_classes = [IsAuthenticated, CanReadAgreementOrders]
    http_method_names = ['get', 'head', 'options']

    def get_orders(self, request, kind, pk):
        agreement, relations = agreement_scope(kind, pk)
        # Planning visibility applies even to Admin and users with other permissions.
        if request.query_params.get('scope') == 'planning' and agreement.is_hidden:
            raise NotFound()
        return DisbursementOrder.objects.filter(is_removed=False, **relations)


class AgreementOrderListView(AgreementOrderReadView):
    def get(self, request, kind, pk):
        orders = self.get_orders(request, kind, pk).select_related('created_by', 'updated_by')
        data = []
        scope = request.query_params.get('scope', 'agreement')
        for order in orders:
            item = serialize_order(order, request, kind, pk)
            url = reverse('agreement-order-file', kwargs={'kind': kind, 'pk': pk, 'order_id': order.pk}, request=request)
            item['downloadUrl'] = f'{url}?scope={scope}'
            data.append(item)
        return success_response(request=request, code='request.success', data=data,
                                total_count=len(data), page_size=len(data))


class AgreementOrderFileView(AgreementOrderReadView):
    def get(self, request, kind, pk, order_id):
        from contract.file_access import consume_download_grant
        get_object_or_404(self.get_orders(request, kind, pk), pk=order_id)
        return consume_download_grant(request, kind=kind, pk=pk, order_id=order_id)
