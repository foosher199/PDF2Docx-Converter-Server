"""错误码：与主服务 api/errors.py 对齐，供 HTTP 响应与 Worker 解析。"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException


class ErrorCode:
    FILE_NOT_PDF = "FILE_NOT_PDF"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    PDF_INVALID = "PDF_INVALID"
    PDF_NO_PAGES = "PDF_NO_PAGES"
    PDF_PAGES_EXCEEDED = "PDF_PAGES_EXCEEDED"
    CONVERSION_FAILED = "CONVERSION_FAILED"
    CONVERTER_BUSY = "CONVERTER_BUSY"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def error_detail(code: str, **params: Any) -> dict[str, Any]:
    cleaned = {key: value for key, value in params.items() if value is not None}
    payload: dict[str, Any] = {"code": code}
    if cleaned:
        payload["params"] = cleaned
    return payload


def api_error(
    status_code: int,
    code: str,
    *,
    headers: Optional[dict[str, str]] = None,
    **params: Any,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=error_detail(code, **params),
        headers=headers,
    )
