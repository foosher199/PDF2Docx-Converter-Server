#!/usr/bin/env python3
"""
独立 PDF → Word 转换微服务（AGPL 隔离）
使用 pdf2docx (MIT) + PyMuPDF (AGPL-3.0)
本服务必须单独进程部署，AGPL 仅约束此服务自身源码
"""

import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from converter import pdf_to_word, check_pdf_valid

app = FastAPI(
    title="PDF Converter Service",
    description="PDF to Word conversion microservice. AGPL isolated.",
    version="1.0.0",
)

MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "52428800"))  # default 50MB
CHUNK_SIZE = 64 * 1024  # 64KB
MAX_PAGES = int(os.environ.get("MAX_PAGES", "100"))


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "converter"}


@app.post("/convert")
def convert_pdf(file: UploadFile = File(...)):
    """
    上传 PDF，返回转换后的 docx 文件
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    tmpdir = tempfile.mkdtemp()
    pdf_path = os.path.join(tmpdir, "input.pdf")
    output_path = os.path.join(tmpdir, "output.docx")

    try:
        # 分块流式写入磁盘，并限制总大小
        total_size = 0
        with open(pdf_path, "wb") as pdf_file:
            while chunk := file.file.read(CHUNK_SIZE):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        413,
                        f"文件大小超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制"
                    )
                pdf_file.write(chunk)

        # 校验 PDF（含页数限制）
        valid, msg = check_pdf_valid(pdf_path, max_pages=MAX_PAGES)
        if not valid:
            raise HTTPException(400, msg)

        # 执行转换
        success, result = pdf_to_word(pdf_path, output_path)
        if not success:
            raise HTTPException(500, result)

    except HTTPException:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, f"转换异常: {str(exc)}")

    # 成功时通过 BackgroundTask 在响应发送后清理临时目录
    return FileResponse(
        result,
        filename=os.path.basename(result),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=BackgroundTask(shutil.rmtree, tmpdir, ignore_errors=True),
    )
