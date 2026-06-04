#!/usr/bin/env python3
"""
PDF → Word 转换模块（pdf2docx）
仅用于独立转换微服务（AGPL 隔离）
"""

import os
import traceback
from pathlib import Path
from typing import Optional, Callable

import pypdfium2 as pdfium
from pdf2docx import Converter


ProgressCallback = Optional[Callable[[int, str], None]]


def check_pdf_valid(pdf_path: str) -> tuple[bool, str]:
    """检查 PDF 文件是否有效"""
    if not os.path.exists(pdf_path):
        return False, f"文件不存在: {pdf_path}"
    if not pdf_path.lower().endswith('.pdf'):
        return False, "文件必须是 PDF 格式"
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        page_count = len(pdf)
        pdf.close()
        if page_count == 0:
            return False, "PDF 没有页面"
        return True, f"PDF 有效，共 {page_count} 页"
    except Exception as e:
        return False, f"PDF 解析失败: {str(e)}"


def pdf_to_word(pdf_path: str, output_path: str, progress_callback: ProgressCallback = None) -> tuple[bool, str]:
    """
    PDF 转 Word (docx)
    使用 pdf2docx (MIT)，依赖 PyMuPDF (AGPL-3.0)
    """
    try:
        if progress_callback:
            progress_callback(0, "开始转换 PDF → Word...")

        if progress_callback:
            progress_callback(20, "正在解析 PDF...")

        def on_progress(current: int, total: int):
            if progress_callback and total > 0:
                pct = int((current / total) * 70) + 20
                progress_callback(pct, f"正在转换第 {current}/{total} 页...")

        cv = Converter(pdf_path)
        cv.convert(output_path, callback=on_progress)
        cv.close()

        if progress_callback:
            progress_callback(100, "转换完成")

        return True, output_path
    except Exception as e:
        return False, f"Word 转换失败: {str(e)}\n{traceback.format_exc()}"
