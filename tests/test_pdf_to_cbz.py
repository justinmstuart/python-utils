"""Tests for scripts/pdf_to_cbz.py."""

import zipfile

from scripts import pdf_to_cbz
from tests.test_helpers import run_cli_with_env


class DummyImage:
    """Simple image test double that writes bytes on save."""

    def __init__(self, marker):
        self.marker = marker

    def save(self, output_path, _format):
        """Write marker bytes to the output path."""
        with open(output_path, "wb") as file:
            file.write(self.marker)


def test_convert_pdf_to_image_directory_uses_expected_filenames(monkeypatch, tmp_path):
    """Pages should be saved as <pdf_name>_001.png style names."""
    pdf_path = tmp_path / "Book Name.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        pdf_to_cbz,
        "convert_from_path",
        lambda _: [DummyImage(b"page1"), DummyImage(b"page2")],
    )

    output_directory = pdf_to_cbz.convert_pdf_to_image_directory(str(pdf_path))

    assert (tmp_path / "Book Name" / "Book Name_001.png").exists()
    assert (tmp_path / "Book Name" / "Book Name_002.png").exists()
    assert output_directory == str(tmp_path / "Book Name")


def test_convert_pdf_to_cbz_runs_cbz_processor(monkeypatch, tmp_path):
    """Conversion should end by invoking CBZ compression on generated archive."""
    pdf_path = tmp_path / "comic.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    image_directory = tmp_path / "comic"
    image_directory.mkdir()
    (image_directory / "comic_001.png").write_bytes(b"img")

    monkeypatch.setattr(
        pdf_to_cbz,
        "convert_pdf_to_image_directory",
        lambda _: str(image_directory),
    )

    captured = {}

    def fake_compress_cbz(path, quality, max_height):
        captured["path"] = path
        captured["quality"] = quality
        captured["max_height"] = max_height
        return 0.0

    monkeypatch.setattr(pdf_to_cbz, "compress_cbz", fake_compress_cbz)

    cbz_path = pdf_to_cbz.convert_pdf_to_cbz(str(pdf_path), quality=75, max_height=900)

    assert cbz_path.endswith(".cbz")
    assert captured == {"path": cbz_path, "quality": 75, "max_height": 900}
    assert (tmp_path / "comic.cbz").exists()
    assert not (tmp_path / "comic.zip").exists()


def test_process_pdf_files_recurses_and_skips_non_pdf(monkeypatch, tmp_path):
    """Only PDF files should be processed while others are counted as skipped."""
    nested = tmp_path / "nested"
    nested.mkdir()
    pdf_file = nested / "book.pdf"
    text_file = nested / "notes.txt"
    pdf_file.write_bytes(b"%PDF-1.4")
    text_file.write_text("skip")

    seen = []
    monkeypatch.setattr(pdf_to_cbz, "convert_pdf_to_cbz", lambda path, **_kwargs: seen.append(path))

    result = pdf_to_cbz.process_pdf_files(str(tmp_path))

    assert seen == [str(pdf_file)]
    assert result["success_count"] == 1
    assert result["skipped_count"] == 1
    assert result["failed_count"] == 0


def test_process_pdf_files_counts_failures(monkeypatch, tmp_path):
    """Failed PDF conversions should increment failed_count and continue."""
    pdf_file = tmp_path / "broken.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    def fake_convert(*_args, **_kwargs):
        raise RuntimeError("bad pdf")

    monkeypatch.setattr(pdf_to_cbz, "convert_pdf_to_cbz", fake_convert)

    result = pdf_to_cbz.process_pdf_files(str(tmp_path))

    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 1


def test_zip_directory_stores_relative_paths(tmp_path):
    """Zip archive should preserve relative paths from the image directory root."""
    image_directory = tmp_path / "series"
    nested = image_directory / "chapter1"
    nested.mkdir(parents=True)
    (nested / "series_001.png").write_bytes(b"img")

    zip_path = pdf_to_cbz.zip_directory(str(image_directory))
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        assert "chapter1/series_001.png" in zip_file.namelist()


def test_cli_entry(tmp_path):
    """CLI module execution should run with PDF_TO_CBZ_DIR set."""
    env_vars = {"PDF_TO_CBZ_DIR": str(tmp_path)}
    result = run_cli_with_env("scripts.pdf_to_cbz", env_vars)
    assert result is not None
    assert result.returncode == 0
