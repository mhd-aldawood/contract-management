import logging

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response

from .responses import ERROR_CODES_BY_STATUS, failure_payload


logger = logging.getLogger("contract.api")


def api_exception_handler(exc, context):
    """Django REST Framework equivalent of the school's global advice handler."""
    request = context.get("request")
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.error(
            "Unhandled API exception",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return Response(
            failure_payload(
                request=request,
                code="server.internal_error",
            ),
            status=500,
        )

    code = ERROR_CODES_BY_STATUS.get(
        response.status_code,
        "request.failed",
    )
    original_errors = response.data
    response.data = failure_payload(
        request=request,
        code=code,
        errors=original_errors,
    )
    return response
