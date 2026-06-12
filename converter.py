#!/usr/bin/env python3
"""
PDF → Word 转换模块（pdf2docx）
仅用于独立转换微服务（AGPL 隔离）
"""

import os
import traceback
from typing import Optional, Callable

import pypdfium2 as pdfium
from pdf2docx import Converter


ProgressCallback = Optional[Callable[[int, str], None]]


def get_pdf_page_count(pdf_path: str) -> tuple[int | None, str | None, dict]:
    """成功 (count, None, {})；失败 (None, error_code, params)。"""
    if not os.path.exists(pdf_path):
        return None, "PDF_INVALID", {}
    if not pdf_path.lower().endswith(".pdf"):
        return None, "FILE_NOT_PDF", {}
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        page_count = len(pdf)
        pdf.close()
        if page_count == 0:
            return None, "PDF_NO_PAGES", {}
        return page_count, None, {}
    except Exception:
        return None, "PDF_INVALID", {}


def check_pdf_valid(pdf_path: str, max_pages: int | None = None) -> tuple[bool, str | None, dict]:
    """校验 PDF。成功 (True, None, {})；失败 (False, error_code, params)。"""
    page_count, error_code, params = get_pdf_page_count(pdf_path)
    if error_code:
        return False, error_code, params
    if max_pages is not None and page_count > max_pages:
        return False, "PDF_PAGES_EXCEEDED", {"limit": max_pages, "actual": page_count}
    return True, None, {}


def pdf_to_word(
    pdf_path: str,
    output_path: str,
    progress_callback: ProgressCallback = None,
) -> tuple[bool, str | None, dict]:
    """成功 (True, None, {})；失败 (False, error_code, params)。"""
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

        return True, None, {}
    except Exception as exc:
        print(f"Word conversion failed: {exc}\n{traceback.format_exc()}")
        return False, "CONVERSION_FAILED", {}
