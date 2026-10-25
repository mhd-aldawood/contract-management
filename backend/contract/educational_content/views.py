# educational_contents/views.py
import json
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.views import APIView

from contract.api.responses import success_response
from contract.rbac import HasFeaturePermission
from .models import EducationalContent
from .serializers import EducationalContentSerializer


def _extract_payload(request):
    """
    Accepts either:
      - application/json
      - multipart/form-data with `data=<json string>`
    """
    raw = request.data.get("data")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return request.data
    return request.data


def _handle_upload(instance, uploaded_file):
    """Attach file, keep original + stored names."""
    if not uploaded_file:
        return
    instance.file = uploaded_file              # FileField uses upload_to_path → uuid name
    instance.original_name = uploaded_file.name
    # after .save(), instance.file.name contains the uuid-relative path
    instance.save()
    # store just the basename for convenience
    instance.stored_name = instance.file.name.rsplit("/", 1)[-1]
    instance.save(update_fields=["stored_name"])


class EducationalContentListCreateView(APIView):
    """
    GET  /api/educational-contents/    → list (supports ?type=...)
    POST /api/educational-contents/    → create
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [HasFeaturePermission]
    feature_code = 'educational-content'

    def get(self, request):
        qs = EducationalContent.objects.all()
        content_type = request.query_params.get("type")
        if content_type:
            qs = qs.filter(type=content_type)
        serializer = EducationalContentSerializer(qs, many=True, context={"request": request})
        return success_response(
            request=request,
            code="request.success",
            data=serializer.data,
            total_count=qs.count(),
            page_size=qs.count(),
        )

    def post(self, request):
        payload = _extract_payload(request)
        uploaded_file = request.FILES.get("file")

        data = payload.dict() if hasattr(payload, "dict") else dict(payload)
        if uploaded_file:
            data["file"] = uploaded_file  # DRF will save it
            data["fileName"] = uploaded_file.name

        serializer = EducationalContentSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # One save. DRF writes the file, runs upload_to, stores original_name.
        instance = serializer.save()
        # store basename after upload_to has run

        if instance.file:
            instance.stored_name = instance.file.name.rsplit("/", 1)[-1]
            instance.save(update_fields=["stored_name"])

        data = EducationalContentSerializer(instance, context={"request": request}).data
        return success_response(
            request=request,
            code="agreement.educational_content.created",
            data=data,
            status_code=status.HTTP_201_CREATED,
        )


class EducationalContentDetailView(APIView):
    """
    GET/PUT/PATCH/DELETE /api/educational-contents/<pk>/
    """
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [HasFeaturePermission]
    feature_code = 'educational-content'

    def _get_object(self, pk):
        try:
            return EducationalContent.objects.get(pk=pk)
        except EducationalContent.DoesNotExist:
            return None

    def get(self, request, pk):
        instance = self._get_object(pk)
        if not instance:
            raise NotFound()
        return success_response(
            request=request,
            code="request.success",
            data=EducationalContentSerializer(instance, context={"request": request}).data,
        )

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        instance = self._get_object(pk)
        if not instance:
            raise NotFound()

        payload = _extract_payload(request)
        uploaded_file = request.FILES.get("file")

        serializer = EducationalContentSerializer(
            instance, data=payload, partial=partial, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        instance = serializer.save()
        _handle_upload(instance, uploaded_file)

        return success_response(
            request=request,
            code="agreement.educational_content.updated",
            data=EducationalContentSerializer(instance, context={"request": request}).data,
        )

    def delete(self, request, pk):
        instance = self._get_object(pk)
        if not instance:
            raise NotFound()
        # optional: delete the file from storage
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
        return success_response(
            request=request,
            code="agreement.educational_content.deleted",
        )


class EducationalContentUploadView(APIView):
    """
    POST /api/educational-contents/upload/
    FormData: file=<binary>, content_id=<optional>

    If content_id is given → attaches to that record.
    Otherwise → returns the file path + url + uuid name (no record created).
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [HasFeaturePermission]
    feature_code = 'educational-content'

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            raise ValidationError({"file": ["لم يتم إرسال أي ملف"]})

        content_id = request.data.get("content_id")

        if content_id:
            try:
                content = EducationalContent.objects.get(pk=content_id)
            except EducationalContent.DoesNotExist:
                raise NotFound()

            _handle_upload(content, uploaded)
            return success_response(
                request=request,
                code="agreement.educational_content.file_uploaded",
                data={
                    "id": content.id,
                    "fileName": content.original_name,
                    "storedName": content.stored_name,
                    "url": request.build_absolute_uri(content.file.url),
                },
            )

        # no record yet — save to a temp model so we can return a URL
        # (adjust to your storage strategy)
        raise ValidationError({"content_id": ["content_id مطلوب"]})
