"""Tests for scripts/cbz_clean_up.py."""

import os

import scripts.cbz_clean_up as cbz_clean_up
from tests.test_helpers import run_cli_with_env


def test_cleanup_deletes_matching_files(tmp_path):
    """Delete only files ending in '_original.cbz'."""
    keep_file = tmp_path / "book.cbz"
    delete_file = tmp_path / "book_original.cbz"
    non_cbz_file = tmp_path / "book_original.txt"

    keep_file.write_text("keep")
    delete_file.write_text("delete")
    non_cbz_file.write_text("keep")

    result = cbz_clean_up.clean_up_original_cbz_files(str(tmp_path))

    assert result["success_count"] == 1
    assert result["skipped_count"] == 2
    assert result["failed_count"] == 0
    assert keep_file.exists()
    assert not delete_file.exists()
    assert non_cbz_file.exists()


def test_cleanup_is_recursive(tmp_path):
    """Delete matching files from nested subdirectories."""
    nested = tmp_path / "nested" / "deeper"
    nested.mkdir(parents=True)
    delete_file = nested / "comic_original.cbz"
    keep_file = nested / "comic.cbz"

    delete_file.write_text("delete")
    keep_file.write_text("keep")

    result = cbz_clean_up.clean_up_original_cbz_files(str(tmp_path))

    assert result["success_count"] == 1
    assert result["skipped_count"] == 1
    assert result["failed_count"] == 0
    assert not delete_file.exists()
    assert keep_file.exists()


def test_cleanup_does_not_delete_non_matching_original_names(tmp_path):
    """Do not delete files that only contain '_original' as a substring."""
    files = [
        tmp_path / "book_original_backup.cbz",
        tmp_path / "book.cbz",
        tmp_path / "book_originals.cbz",
        tmp_path / "other.txt",
    ]
    for file_path in files:
        file_path.write_text("keep")

    result = cbz_clean_up.clean_up_original_cbz_files(str(tmp_path))

    assert result["success_count"] == 0
    assert result["skipped_count"] == 4
    assert result["failed_count"] == 0
    for file_path in files:
        assert file_path.exists()


def test_cleanup_matches_case_insensitive_extension(tmp_path):
    """Delete '_original.CBZ' with uppercase extension."""
    delete_file = tmp_path / "book_original.CBZ"
    delete_file.write_text("delete")

    result = cbz_clean_up.clean_up_original_cbz_files(str(tmp_path))

    assert result["success_count"] == 1
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0
    assert not delete_file.exists()


def test_cleanup_continue_on_delete_error(monkeypatch, tmp_path):
    """Continue scanning and report failed_count when os.remove raises OSError."""
    failing_file = tmp_path / "bad_original.cbz"
    deleted_file = tmp_path / "good_original.cbz"
    skipped_file = tmp_path / "keep.cbz"

    failing_file.write_text("delete")
    deleted_file.write_text("delete")
    skipped_file.write_text("keep")

    original_remove = os.remove

    def fake_remove(path):
        if path == str(failing_file):
            raise OSError("permission denied")
        return original_remove(path)

    monkeypatch.setattr(cbz_clean_up.os, "remove", fake_remove)

    result = cbz_clean_up.clean_up_original_cbz_files(str(tmp_path))

    assert result["success_count"] == 1
    assert result["skipped_count"] == 1
    assert result["failed_count"] == 1
    assert failing_file.exists()
    assert not deleted_file.exists()
    assert skipped_file.exists()


def test_main_uses_cbz_processor_env_var(monkeypatch, tmp_path):
    """main() should use CBZ_PROCESSOR_DIR without prompting."""
    delete_file = tmp_path / "series_original.cbz"
    delete_file.write_text("delete")

    monkeypatch.setenv("CBZ_PROCESSOR_DIR", str(tmp_path))

    captured = {}

    def fake_print_result(stats, _titles):
        captured["stats"] = stats

    monkeypatch.setattr(cbz_clean_up, "print_result", fake_print_result)

    cbz_clean_up.main()

    assert captured["stats"]["success_count"] == 1
    assert not delete_file.exists()


def test_cli_entry(tmp_path):
    """CLI module execution should run with CBZ_PROCESSOR_DIR set."""
    env_vars = {"CBZ_PROCESSOR_DIR": str(tmp_path)}
    result = run_cli_with_env("scripts.cbz_clean_up", env_vars)
    assert result is not None
    assert result.returncode == 0
