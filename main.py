#!/usr/bin/env python3
"""
独立 PDF → Word 转换微服务（AGPL 隔离）
使用 pdf2docx (MIT) + PyMuPDF (AGPL-3.0)
本服务必须单独进程部署，AGPL 仅约束此服务自身源码
"""

import os
import shutil
import tempfile
import threading

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from converter import pdf_to_word, check_pdf_valid
from errors import ErrorCode, api_error

app = FastAPI(
    title="PDF Converter Service",
    description="PDF to Word conversion microservice. AGPL isolated.",
    version="1.0.0",
)

MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", str(50 * 1024 * 1024)))
CHUNK_SIZE = 64 * 1024
# 兜底页数上限（主 API 已按用户权益校验；此处仅防异常请求）
MAX_PAGES = int(os.environ.get("MAX_PAGES", "200"))
MAX_CONCURRENT_CONVERSIONS = int(os.environ.get("MAX_CONCURRENT_CONVERSIONS", "2"))

convert_semaphore = threading.Semaphore(MAX_CONCURRENT_CONVERSIONS)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "converter"}


@app.post("/convert")
def convert_pdf(file: UploadFile = File(...)):
    """
    上传 PDF，返回转换后的 docx 文件。
    错误响应：{"detail": {"code": "...", "params": {...}}}
    """
    if not file.filename.lower().endswith(".pdf"):
        raise api_error(400, ErrorCode.FILE_NOT_PDF)

    if not convert_semaphore.acquire(blocking=False):
        raise api_error(503, ErrorCode.CONVERTER_BUSY)

    tmpdir = tempfile.mkdtemp()
    pdf_path = os.path.join(tmpdir, "input.pdf")
    output_path = os.path.join(tmpdir, "output.docx")

    try:
        total_size = 0
        with open(pdf_path, "wb") as pdf_file:
            while chunk := file.file.read(CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    limit_mb = MAX_FILE_SIZE // 1024 // 1024
                    raise api_error(413, ErrorCode.FILE_TOO_LARGE, limit_mb=limit_mb)
                pdf_file.write(chunk)

        valid, error_code, error_params = check_pdf_valid(pdf_path, max_pages=MAX_PAGES)
        if not valid and error_code:
            status = 413 if error_code == ErrorCode.PDF_PAGES_EXCEEDED else 400
            raise api_error(status, error_code, **error_params)

        success, fail_code, fail_params = pdf_to_word(pdf_path, output_path)
        if not success:
            raise api_error(500, fail_code or ErrorCode.CONVERSION_FAILED, **fail_params)

    except HTTPException:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise api_error(500, ErrorCode.INTERNAL_ERROR) from exc
    finally:
        convert_semaphore.release()

    return FileResponse(
        output_path,
        filename=os.path.basename(output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=BackgroundTask(shutil.rmtree, tmpdir, ignore_errors=True),
    )
