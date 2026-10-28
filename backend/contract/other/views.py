from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status

from contract.api.responses import success_response
from contract.rbac import HasFeaturePermission
from contract.order_counts import with_order_counts
from contract.other.models import Agreement
from contract.other.serializers import AgreementSerializer


class AgreementCreateView(generics.CreateAPIView):
    queryset = Agreement.objects.all()
    serializer_class = AgreementSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [HasFeaturePermission]
    feature_code = 'other-agreements'
    agreement_type = 'other-agreements'

    def perform_create(self, serializer):
        serializer.save(type=self.agreement_type)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            request=request,
            code="agreement.other.created",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class AgreementListView(generics.ListAPIView):
    serializer_class = AgreementSerializer
    permission_classes = [HasFeaturePermission]
    feature_code = 'other-agreements'
    agreement_type = 'other-agreements'

    def get(self, request, *args, **kwargs):
        agreements = with_order_counts(Agreement.objects.filter(type=self.agreement_type), request).prefetch_related('rows')
        data = self.get_serializer(agreements, many=True).data
        return success_response(request=request, code='request.success', data=data,
                                total_count=len(data), page_size=len(data))


class MemorandumCreateView(AgreementCreateView):
    feature_code = 'memorandum'
    agreement_type = 'memorandum'


class MemorandumListView(AgreementListView):
    feature_code = 'memorandum'
    agreement_type = 'memorandum'
