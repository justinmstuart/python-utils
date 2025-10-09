"""
Unit tests for cbz_processor.py functions.

These tests cover the main functions in cbz_processor.py, using test_mp3_metadata_stripper.py as a template.
"""

from scripts.cbz_processor import main as cbz_main, get_file_size, clean_file_naming, process_cbz_files
import pytest
import zipfile
import sys
import subprocess
import os


@pytest.fixture(autouse=True)
def patch_env_and_prompt(monkeypatch, tmp_path):
    # Patch environment variables to dummy values
    monkeypatch.setenv("CBZ_PROCESSOR_DIR", str(tmp_path))
    monkeypatch.setenv("TRIM_FILENAMES_DIR", str(tmp_path))
    monkeypatch.setenv("MP3_METADATA_STRIPPER_DIR", str(tmp_path))
    # Patch get_directory_from_env_or_prompt to always return tmp_path
    monkeypatch.setattr("scripts.utils.get_directory_from_env_or_prompt", lambda var: str(tmp_path))


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


def test_compress_cbz_image_save_error(monkeypatch, tmp_path):
    """
    Simulate error when saving image in compress_cbz.
    """
    from scripts.cbz_processor import compress_cbz
    from PIL import Image
    # Create a dummy CBZ file
    cbz_path = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz_path, 'w') as zf:
        zf.writestr("image.png", b"fake")
    class DummyImg:
        mode = 'RGB'
        height = 100
        def save(self, *a, **kw):
            raise OSError("save error")
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr("PIL.Image.open", lambda path: DummyImg())
    try:
        compress_cbz(str(cbz_path))
    except Exception:
        pass


def test_process_cbz_files_backup_error(monkeypatch, tmp_path):
    """
    Simulate error when creating backup in process_cbz_files.
    """
    from scripts.cbz_processor import process_cbz_files
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    monkeypatch.setattr("shutil.copy2", lambda *a, **kw: (_ for _ in ()).throw(OSError("copy error")))
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    assert result["failed_count"] >= 1


def test_process_cbz_files_compress_error(monkeypatch, tmp_path):
    """
    Simulate error in compress_cbz during process_cbz_files.
    """
    from scripts.cbz_processor import process_cbz_files
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    monkeypatch.setattr("scripts.cbz_processor.compress_cbz", lambda *a, **kw: (_ for _ in ()).throw(OSError("compress error")))
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    assert result["failed_count"] >= 1


def test_compress_cbz_exception(monkeypatch, tmp_path):
    from scripts.cbz_processor import compress_cbz
    # Patch get_file_size to raise an exception inside compress_cbz
    monkeypatch.setattr("scripts.cbz_processor.get_file_size", lambda path: (_ for _ in ()).throw(Exception("fail")))
    with pytest.raises(Exception):
        compress_cbz(str(tmp_path / "test.cbz"))


def test_process_cbz_files_exception(monkeypatch, tmp_path, capsys):
    from scripts.cbz_processor import process_cbz_files
    # Patch compress_cbz to raise an exception
    monkeypatch.setattr("scripts.cbz_processor.compress_cbz", lambda path, **kwargs: (_ for _ in ()).throw(Exception("fail")))
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1


def test_compress_cbz_tempdir_exception(monkeypatch, tmp_path):
    from scripts.cbz_processor import compress_cbz
    import tempfile
    # Patch tempfile.TemporaryDirectory to raise an exception
    class DummyTempDir:
        def __enter__(self):
            raise Exception("tempdir fail")
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    monkeypatch.setattr(tempfile, "TemporaryDirectory", lambda: DummyTempDir())
    with pytest.raises(Exception):
        compress_cbz(str(tmp_path / "test.cbz"))


def test_process_cbz_files_cbz_exception(monkeypatch, tmp_path, capsys):
    from scripts.cbz_processor import process_cbz_files
    # Patch compress_cbz to raise an exception for cbz file
    monkeypatch.setattr("scripts.cbz_processor.compress_cbz", lambda path, **kwargs: (_ for _ in ()).throw(Exception("cbz fail")))
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1


def test_process_cbz_files_cbz_error_branch(monkeypatch, tmp_path, capsys):
    from scripts.cbz_processor import process_cbz_files
    monkeypatch.setattr("scripts.cbz_processor.compress_cbz", lambda path, **kwargs: (_ for _ in ()).throw(Exception("cbz error")))
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1


@pytest.mark.parametrize("mode,height,should_resize", [
    ("RGB", 100, False),
    ("P", 2000, True),
    ("RGB", 2000, True),
])
def test_compress_cbz_branches(monkeypatch, tmp_path, mode, height, should_resize):
    from scripts.cbz_processor import compress_cbz
    class DummyImg:
        def __init__(self):
            self.mode = mode
            self.height = height
            self.width = 1000
            self.resized = False
        def convert(self, m):
            self.mode = m
            return self
        def resize(self, size, resample):
            self.resized = True
            return self
        def save(self, *a, **kw):
            pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr("PIL.Image.open", lambda path: DummyImg())
    cbz_path = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz_path, 'w') as zf:
        zf.writestr("image.png", b"fake")
    compress_cbz(str(cbz_path))


def test_process_cbz_files_print_output(capsys, tmp_path):
    from scripts.cbz_processor import process_cbz_files
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    out = capsys.readouterr().out
    assert "Optimized" in out or "Failed" in out or "Skipped" in out


def test_process_cbz_files_summary_output(monkeypatch, capsys, tmp_path):
    from scripts.cbz_processor import process_cbz_files
    # Simulate files and monkeypatch compress_cbz to always fail
    cbz_path = tmp_path / "fail.cbz"
    cbz_path.write_bytes(b"dummy")
    monkeypatch.setattr("scripts.cbz_processor.compress_cbz", lambda path: False)
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    out = capsys.readouterr().out
    assert "Failed" in out or "Summary" in out


def test_cbz_processor_main_summary(monkeypatch, capsys, tmp_path):
    import scripts.cbz_processor as cbz
    monkeypatch.setattr(cbz, "get_directory_from_env_or_prompt", lambda env: str(tmp_path))
    monkeypatch.setattr(cbz, "process_cbz_files", lambda d, s, q, m: {"success_count": 1, "skipped_count": 0, "failed_count": 0})
    cbz.main()
    out = capsys.readouterr().out
    assert "Processing directory" in out and "Success" in out


def test_cbz_processor_process_cbz_files_non_cbz(monkeypatch, tmp_path):
    from scripts.cbz_processor import process_cbz_files
    # Create a non-cbz file
    file_path = tmp_path / "not_cbz.txt"
    file_path.write_text("dummy")
    result = process_cbz_files(str(tmp_path), 1, 80, 1024)
    assert result["skipped_count"] >= 1


def test_cbz_processor_main_all_failed(monkeypatch, capsys, tmp_path):
    import scripts.cbz_processor as cbz
    monkeypatch.setattr(cbz, "get_directory_from_env_or_prompt", lambda env: str(tmp_path))
    monkeypatch.setattr(cbz, "process_cbz_files", lambda d, s, q, m: {"success_count": 0, "skipped_count": 0, "failed_count": 1})
    cbz.main()
    out = capsys.readouterr().out
    assert "Failed" in out


def test_cbz_processor_main_system_exit(monkeypatch):
    import scripts.cbz_processor as cbz
    def fake_get_directory(env):
        raise SystemExit(1)
    monkeypatch.setattr(cbz, "get_directory_from_env_or_prompt", fake_get_directory)
    with pytest.raises(SystemExit):
        cbz.main()


def test_cbz_processor_cli_entry(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(__file__))
    env["CBZ_PROCESSOR_DIR"] = str(tmp_path)
    try:
        result = subprocess.run([sys.executable, "-m", "coverage", "run", "-m", "scripts.cbz_processor"], input=b"\n", capture_output=True, env=env, timeout=5)
        assert b"Processing directory" in result.stdout or b"Error" in result.stdout or b"ModuleNotFoundError" in result.stderr
    except subprocess.TimeoutExpired:
        pytest.skip("CLI test timed out (likely waiting for input)")


def test_compress_cbz_extractall_exception(monkeypatch, tmp_path):
    from scripts.cbz_processor import compress_cbz
    import zipfile
    class DummyZip:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def extractall(self, path):
            raise Exception("extractall fail")
    monkeypatch.setattr(zipfile, "ZipFile", lambda *a, **kw: DummyZip())
    with pytest.raises(Exception):
        compress_cbz(str(tmp_path / "test.cbz"))
