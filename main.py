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

    content = file.file.read()
    with open(pdf_path, "wb") as f:
        f.write(content)

    # 校验 PDF
    valid, msg = check_pdf_valid(pdf_path)
    if not valid:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(400, msg)

    # 执行转换
    success, result = pdf_to_word(pdf_path, output_path)
    if not success:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(500, result)

    return FileResponse(
        result,
        filename=os.path.basename(result),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=BackgroundTask(shutil.rmtree, tmpdir, ignore_errors=True),
    )
