"""Tests for scripts/pdf_to_txt.py."""

from scripts import pdf_to_txt
from tests.test_helpers import run_cli_with_env


def make_pdf_bytes(text):
    """Build a minimal single-page PDF containing the given text."""
    content_stream = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        (
            b"<< /Length "
            + str(len(content_stream)).encode()
            + b" >>\nstream\n"
            + content_stream
            + b"\nendstream"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n".encode()
    output += b"0000000000 65535 f \n"
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    output += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return bytes(output)


class DummyPage:
    """Simple page test double that returns canned text."""

    def __init__(self, text, layout_error=False):
        self.text = text
        self.layout_error = layout_error

    def extract_text(self, layout=False):
        """Return canned text, raising for layout mode when configured."""
        if layout and self.layout_error:
            raise ValueError("layout failed")
        return self.text


class DummyPdf:
    """Simple pdf test double exposing a pages list."""

    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_convert_pdf_to_txt_writes_text_next_to_pdf(monkeypatch, tmp_path):
    """Conversion should write a .txt file next to the source PDF."""
    pdf_path = tmp_path / "story.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        pdf_to_txt,
        "pdfplumber",
        type("M", (), {"open": staticmethod(lambda _: DummyPdf([DummyPage("Hello"), DummyPage("World")]))}),
    )

    txt_path = pdf_to_txt.convert_pdf_to_txt(str(pdf_path))

    assert txt_path == str(tmp_path / "story.txt")
    assert (tmp_path / "story.txt").read_text(encoding="utf-8") == "Hello\n\nWorld"
    assert pdf_path.exists()


def test_extract_text_from_pdf_falls_back_when_layout_fails(monkeypatch, tmp_path):
    """Layout extraction failures should fall back to default extraction."""
    pdf_path = tmp_path / "story.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        pdf_to_txt,
        "pdfplumber",
        type(
            "M",
            (),
            {"open": staticmethod(lambda _: DummyPdf([DummyPage("Fallback", layout_error=True)]))},
        ),
    )

    assert pdf_to_txt.extract_text_from_pdf(str(pdf_path)) == "Fallback"


def test_process_pdf_files_recurses_and_skips_non_pdf(monkeypatch, tmp_path):
    """Only PDF files should be processed while others are counted as skipped."""
    pdf_file = tmp_path / "docs" / "book.pdf"
    pdf_file.parent.mkdir()
    text_file = tmp_path / "docs" / "index.txt"
    text_file.write_text("skip")
    pdf_file.write_bytes(b"%PDF-1.4")

    seen = []

    def fake_convert(path):
        seen.append(path)
        return f"{path}.txt"

    monkeypatch.setattr(pdf_to_txt, "convert_pdf_to_txt", fake_convert)

    result = pdf_to_txt.process_pdf_files(str(tmp_path))

    assert result["success_count"] == 1
    assert result["failed_count"] == 0
    assert result["skipped_count"] == 1
    assert seen == [str(pdf_file)]


def test_process_pdf_files_counts_failures(monkeypatch, tmp_path):
    """Failed PDF conversions should increment failed_count and continue."""
    pdf_file = tmp_path / "broken.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    def fake_convert(*_args, **_kwargs):
        raise RuntimeError("bad pdf")

    monkeypatch.setattr(pdf_to_txt, "convert_pdf_to_txt", fake_convert)

    result = pdf_to_txt.process_pdf_files(str(tmp_path))

    assert result["failed_count"] == 1
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0


def test_end_to_end_with_real_pdf(tmp_path):
    """A real minimal PDF should convert to a txt file containing its text."""
    pdf_file = tmp_path / "real.pdf"
    pdf_file.write_bytes(make_pdf_bytes("Hello from PDF"))

    result = pdf_to_txt.process_pdf_files(str(tmp_path))

    assert result["success_count"] == 1
    assert result["failed_count"] == 0
    output = (tmp_path / "real.txt").read_text(encoding="utf-8")
    assert "Hello" in output
    assert "PDF" in output
    assert all(line == line.rstrip() for line in output.splitlines())


def test_cli_entry(tmp_path):
    """CLI module execution should run with PDF_TO_TXT_DIR set."""
    env_vars = {"PDF_TO_TXT_DIR": str(tmp_path)}
    result = run_cli_with_env("scripts.pdf_to_txt", env_vars)
    assert result is not None
    assert result.returncode == 0
