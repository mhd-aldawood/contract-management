from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.rbac import HasFeaturePermission
from contract.order_counts import with_order_counts
from contract.life_long.serializers import LifeLongAgreementSerializer
from contract.life_long.models import LifeLongAgreement


class LifeLongCreateView(APIView):
    """
    POST /api/life-long/create/
    Accepts both application/json and multipart/form-data.
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'lifelong-learning'
    def post(self, request, *args, **kwargs):
        serializer = LifeLongAgreementSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            request=request,
            code='agreement.life_long.created',
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class LifeLongListView(APIView):
    permission_classes = [IsAuthenticated, HasFeaturePermission]
    feature_code = 'lifelong-learning'

    def get(self, request):
        agreements = with_order_counts(LifeLongAgreement.objects.all(), request).prefetch_related('payment_schedule').order_by('-pk')
        data = LifeLongAgreementSerializer(agreements, many=True, context={'request': request}).data
        return success_response(request=request, code='request.success', data=data,
                                total_count=len(data), page_size=len(data))
