from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.rbac import HasFeaturePermission
from contract.order_counts import with_order_counts
from .models import NafathCenterAgreement
from .serializers import NafathCenterAgreementSerializer


class NafathCenterCreateView(APIView):
    """
    POST /api/nafath-center/create/
    Accepts both application/json and multipart/form-data.
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'nafath-centers'
    def post(self, request, *args, **kwargs):
        serializer = NafathCenterAgreementSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            request=request,
            code='agreement.nafath.created',
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class NafathCenterListView(APIView):
    """GET /api/nafath-center/  — list all agreements."""

    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'nafath-centers'

    def get(self, request, *args, **kwargs):
        qs = with_order_counts(NafathCenterAgreement.objects.all(), request).prefetch_related('payment_schedule')
        serializer = NafathCenterAgreementSerializer(
            qs, many=True, context={'request': request}
        )
        return success_response(
            request=request,
            code='request.success',
            data=serializer.data,
            total_count=qs.count(),
            page_size=qs.count(),
        )
