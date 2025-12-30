import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.append(str(src_path))

from features.document.core.converter import DocumentConverter

def test_imports():
    from features.document.core.converter import (
        HAS_PYMUPDF, HAS_PDF2DOCX, HAS_COMTYPES, HAS_MARKDOWN, HAS_PISA, HAS_PIL
    )
    print(f"PyMuPDF: {HAS_PYMUPDF}")
    print(f"pdf2docx: {HAS_PDF2DOCX}")
    print(f"comtypes: {HAS_COMTYPES}")
    print(f"markdown: {HAS_MARKDOWN}")
    print(f"xhtml2pdf: {HAS_PISA}")
    print(f"Pillow: {HAS_PIL}")

def verify_backend():
    print("Testing Backend Logic initialization...")
    conv = DocumentConverter()
    print("Backend initialized successfully.")

if __name__ == "__main__":
    test_imports()
    verify_backend()
