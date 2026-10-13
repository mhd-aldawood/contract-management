from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status

from contract.api.responses import success_response
from contract.other.models import Agreement
from contract.other.serializers import AgreementSerializer


class AgreementCreateView(generics.CreateAPIView):
    queryset = Agreement.objects.all()
    serializer_class = AgreementSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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
