from rest_framework.renderers import JSONRenderer

from .responses import normalize_response_payload


class UnifiedJSONRenderer(JSONRenderer):
    """Guarantee the unified contract for every Django REST Framework response."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        context = renderer_context or {}
        response = context.get("response")
        request = context.get("request")

        if response is not None:
            data = normalize_response_payload(
                request=request,
                data=data,
                status_code=response.status_code,
            )

        return super().render(data, accepted_media_type, context)
