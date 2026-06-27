"""Smoke tests for PDF skill import helpers."""

from io import BytesIO

from pypdf import PdfWriter

from app.services.pdf_skill_import_service import extract_pdf_text, _is_pdf_upload


class _FakeUpload:
    def __init__(self, filename: str, content_type: str) -> None:
        self.filename = filename
        self.content_type = content_type


def _minimal_pdf(text: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = BytesIO()
    writer.write(buf)
    data = buf.getvalue()
    return data


def test_is_pdf_by_filename() -> None:
    upload = _FakeUpload("notes.pdf", "application/octet-stream")
    assert _is_pdf_upload(upload, b"%PDF-1.4 fake")


def test_extract_pdf_empty_pages() -> None:
    data = _minimal_pdf("")
    text, pages = extract_pdf_text(data)
    assert pages == 1
    assert isinstance(text, str)


if __name__ == "__main__":
    test_is_pdf_by_filename()
    test_extract_pdf_empty_pages()
    print("pdf skill import smoke tests passed")