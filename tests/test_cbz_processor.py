"""
Unit tests for cbz_processor.py functions.

These tests cover the main functions in cbz_processor.py, using test_mp3_metadata_stripper.py as a template.
"""

from scripts.cbz_processor import main as cbz_main, get_file_size, clean_file_naming, process_cbz_files


def test_cbz_main_runs(monkeypatch, tmp_path):
    """
    Test that cbz_main runs without error when called (integration smoke test).
    """
    # Create a dummy directory and file structure
    test_dir = tmp_path / "comics"
    test_dir.mkdir()
    (test_dir / "test.cbz").write_bytes(b"dummy data")

    # Patch get_directory_from_env_or_prompt to return our test_dir
    monkeypatch.setattr("scripts.utils.get_directory_from_env_or_prompt", lambda var: str(test_dir))
    # Patch print_result to a no-op to avoid clutter
    monkeypatch.setattr("scripts.utils.print_result", lambda *a, **kw: None)
    # Patch print_newline to a no-op
    monkeypatch.setattr("scripts.utils.print_newline", lambda *a, **kw: None)

    # Should not raise
    cbz_main()


def test_cbz_main_handles_empty_dir(monkeypatch, tmp_path):
    """
    Test that cbz_main handles an empty directory gracefully.
    """
    test_dir = tmp_path / "empty"
    test_dir.mkdir()
    monkeypatch.setattr("scripts.utils.get_directory_from_env_or_prompt", lambda var: str(test_dir))
    monkeypatch.setattr("scripts.utils.print_result", lambda *a, **kw: None)
    monkeypatch.setattr("scripts.utils.print_newline", lambda *a, **kw: None)
    cbz_main()


def test_get_file_size(tmp_path):
    """
    Test get_file_size returns correct size in MB for a file.
    """
    file_path = tmp_path / "file.txt"
    file_path.write_bytes(b"a" * 1048576)  # 1 MB
    size_mb = get_file_size(str(file_path))
    assert 0.99 < size_mb < 1.01


def test_clean_file_naming():
    """
    Test clean_file_naming removes parentheses and adds number.
    """
    filename = "My Comic (2021).cbz"
    cleaned = clean_file_naming(filename, 5)
    assert "(" not in cleaned and ")" not in cleaned
    assert cleaned.endswith("005.cbz")


def test_process_cbz_files_empty(tmp_path):
    """
    Test process_cbz_files returns all skipped for empty dir.
    """
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0


def test_process_cbz_files_skips_non_cbz(tmp_path):
    """
    Test process_cbz_files skips non-cbz files.
    """
    (tmp_path / "not_a_comic.txt").write_text("irrelevant")
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    assert result["skipped_count"] == 1
    assert result["success_count"] == 0
    assert result["failed_count"] == 0
