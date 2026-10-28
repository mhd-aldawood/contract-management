from rest_framework.response import Response

from .message_catalog import resolve_message


ERROR_CODES_BY_STATUS = {
    409: 'file.grant_used',
    410: 'file.grant_expired',
    400: "request.validation_failed",
    401: "auth.unauthenticated",
    403: "auth.permission_denied",
    404: "resource.not_found",
    405: "request.method_not_allowed",
    415: "request.unsupported_media_type",
    429: "request.throttled",
}

RESPONSE_KEYS = {
    "status",
    "code",
    "message",
    "data",
    "totalCount",
    "page",
    "pageSize",
}


def _response_payload(
    *,
    request,
    status,
    code,
    data=None,
    total_count=1,
    page=1,
    page_size=1,
    errors=None,
):
    """Build the response contract shared with the school application."""
    payload = {
        "status": status,
        "code": code,
        "message": resolve_message(code, request),
        "data": data,
        "totalCount": total_count,
        "page": page,
        "pageSize": page_size,
    }
    if errors is not None:
        payload["errors"] = errors
    return payload


def normalize_response_payload(*, request, data, status_code):
    """Normalize any DRF payload, including responses returned by third-party views."""
    if isinstance(data, dict) and RESPONSE_KEYS.issubset(data):
        return data

    if status_code < 400:
        total_count = len(data) if isinstance(data, list) else 1
        return _response_payload(
            request=request,
            status="SUCCESS",
            code="request.success",
            data=data,
            total_count=total_count,
            page=1,
            page_size=total_count,
        )

    code = ERROR_CODES_BY_STATUS.get(status_code, "request.failed")
    return _response_payload(
        request=request,
        status="FAILURE",
        code=code,
        data=None,
        total_count=0,
        page=1,
        page_size=10,
        errors=data,
    )


def success_response(
    *,
    request,
    code,
    data=None,
    status_code=200,
    total_count=1,
    page=1,
    page_size=1,
):
    """Return the stable success envelope consumed by the frontend."""
    return Response(
        _response_payload(
            request=request,
            status="SUCCESS",
            code=code,
            data=data,
            total_count=total_count,
            page=page,
            page_size=page_size,
        ),
        status=status_code,
    )


def failure_payload(*, request, code, errors=None):
    return _response_payload(
        request=request,
        status="FAILURE",
        code=code,
        data=None,
        total_count=0,
        page=1,
        page_size=10,
        errors=errors,
    )
