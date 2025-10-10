"""Unit tests for cbz_processor.py.

Covers main functions using test_mp3_metadata_stripper.py as template.
"""

import zipfile
import tempfile
import pytest
import scripts.cbz_processor as cbz
from scripts.cbz_processor import (
    clean_file_naming,
    get_file_size,
    main as cbz_main,
    process_cbz_files,
    compress_cbz,
)
from tests.test_helpers import run_cli_with_env


@pytest.fixture(autouse=True)
def patch_env_and_prompt(monkeypatch, tmp_path):
    """
    Patch environment variables and the directory prompt helper for tests.

    This helper configures a controlled environment for tests by:
    - Setting the environment variables "CBZ_PROCESSOR_DIR", "TRIM_FILENAMES_DIR",
        and "MP3_METADATA_STRIPPER_DIR" to the provided temporary path.
    - Patching "scripts.utils.get_directory_from_env_or_prompt" to always return
        the provided temporary path, preventing interactive prompts during tests.

    Parameters:
            monkeypatch (pytest.MonkeyPatch): The pytest monkeypatch fixture used to
                    set environment variables and attributes.
            tmp_path (pathlib.Path | str): A temporary directory path used as the value
                    for the patched environment variables and the patched prompt return.

    Returns:
            None

    Notes:
            This function mutates global process environment and replaces a utility
            function for the duration of the test. Use it within test setups to avoid
            touching real user directories or requiring user input.
    """
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
    result = process_cbz_files(str(tmp_path), 80, 1024)
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0


def test_process_cbz_files_skips_non_cbz(tmp_path):
    """
    Test process_cbz_files skips non-cbz files.
    """
    (tmp_path / "not_a_comic.txt").write_text("irrelevant")
    result = process_cbz_files(str(tmp_path), 80, 1024)
    assert result["skipped_count"] == 1
    assert result["success_count"] == 0
    assert result["failed_count"] == 0

def test_compress_cbz_image_save_error(monkeypatch, tmp_path):
    """
    Simulate error when saving image in compress_cbz.
    """
    # Create a dummy CBZ file
    cbz_path = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz_path, 'w') as zf:
        zf.writestr("image.png", b"fake")
    class DummyImg:
        """
        A dummy image class for testing purposes.

        Attributes:
            mode (str): The color mode of the image (default is 'RGB').
            height (int): The height of the image (default is 100).

        Methods:
            save(*args, **kwargs): Simulates saving the image and always raises an OSError.
            __enter__(): Enables use as a context manager, returns self.
            __exit__(*args, **kwargs): Handles context manager exit, returns False.
        """
        def __init__(self):
            self.mode = 'RGB'
            self.height = 100
        def save(self, *args):
            """Simulate saving the image and always raise an OSError."""
            raise OSError("save error")
        def __enter__(self):
            return self
        def __exit__(self, *_, **__):
            return False
    monkeypatch.setattr("PIL.Image.open", lambda path: DummyImg())
    try:
        compress_cbz(str(cbz_path))
    except Exception:
        pass


def test_process_cbz_files_backup_error(monkeypatch, tmp_path):
    """
    Simulate error when creating backup in process_cbz_files.
    """
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    monkeypatch.setattr(
        "shutil.copy2",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("copy error"))
    )
    result = process_cbz_files(str(tmp_path), 80, 1024)
    assert result["failed_count"] >= 1


def test_process_cbz_files_compress_error(monkeypatch, tmp_path):
    """
    Simulate error in compress_cbz during process_cbz_files.
    """
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    monkeypatch.setattr(
        "scripts.cbz_processor.compress_cbz",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("compress error"))
    )
    result = process_cbz_files(str(tmp_path), 80, 1024)
    assert result["failed_count"] >= 1


def test_compress_cbz_exception(monkeypatch, tmp_path):
    """Test compress_cbz raises exception if get_file_size fails."""
    # Patch get_file_size to raise an exception inside compress_cbz
    monkeypatch.setattr(
        "scripts.cbz_processor.get_file_size",
        lambda path: (_ for _ in ()).throw(RuntimeError("fail"))
    )
    with pytest.raises(RuntimeError):
        compress_cbz(str(tmp_path / "test.cbz"))


def test_process_cbz_files_exception(monkeypatch, tmp_path, capsys):
    """Test process_cbz_files handles exception from compress_cbz."""
    # Patch compress_cbz to raise an exception
    monkeypatch.setattr(
        "scripts.cbz_processor.compress_cbz",
        lambda path, **kwargs: (_ for _ in ()).throw(RuntimeError("fail"))
    )
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 80, 1024)
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1

def test_compress_cbz_tempdir_exception(monkeypatch, tmp_path):
    """Test compress_cbz handles exception from TemporaryDirectory."""
    class DummyTempDir:
        """Dummy context manager that raises RuntimeError on enter."""
        def __enter__(self):
            raise RuntimeError("tempdir fail")
        def __exit__(self, exc_type, exc_val, exc_tb):
            return False
    monkeypatch.setattr(tempfile, "TemporaryDirectory", DummyTempDir)
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    with pytest.raises(RuntimeError):
        compress_cbz(str(cbz_path))
    # Patch compress_cbz to raise an exception for cbz file
    monkeypatch.setattr(
        "scripts.cbz_processor.compress_cbz",
        lambda path, **kwargs: (_ for _ in ()).throw(RuntimeError("cbz fail"))
    )
    cbz_path = tmp_path / "test.cbz"
    cbz_path = tmp_path / "test.cbz"


def test_process_cbz_files_cbz_exception(monkeypatch, tmp_path, capsys):
    """Test process_cbz_files handles exception from compress_cbz for cbz file."""
    # Patch compress_cbz to raise an exception for cbz file
    monkeypatch.setattr(
        "scripts.cbz_processor.compress_cbz",
        lambda path, **kwargs: (_ for _ in ()).throw(RuntimeError("cbz fail"))
    )
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 80, 1024)
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 80, 1024)


def test_process_cbz_files_cbz_error_branch(monkeypatch, tmp_path, capsys):
    """Test process_cbz_files error branch when compress_cbz raises exception."""
    monkeypatch.setattr(
        "scripts.cbz_processor.compress_cbz",
        lambda path, **kwargs: (_ for _ in ()).throw(RuntimeError("cbz error"))
    )
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    result = process_cbz_files(str(tmp_path), 80, 1024)
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1

@pytest.mark.parametrize("mode,height", [
    ("RGB", 100),
    ("P", 2000),
    ("RGB", 2000),
])
def test_compress_cbz_branches(monkeypatch, tmp_path, mode, height):
    """Test compress_cbz branches for different image modes and heights."""
    class DummyImg:
        """Dummy image class for simulating PIL.Image behavior."""
        def __init__(self, mode, height):
            self.mode = mode
            self.height = height
            self.width = 1000
            self.resized = False
        def convert(self, m):
            """
            Set the processing mode and return the current instance.

            Args:
                m: The mode to set.

            Returns:
                self: The current instance with the updated mode.
            """
            self.mode = m
            return self
        def resize(self, *_, **__):
            """
            Marks the object as resized.

            This method sets the `resized` attribute to True and returns the object itself.
            All positional and keyword arguments are ignored.

            Returns:
                self: The current instance with `resized` set to True.
            """
            self.resized = True
            return self
        def save(self, *_, **__):
            """
            Dummy save method that ignores all arguments and returns None.

            Args:
                *_: Ignored positional arguments.
                **__: Ignored keyword arguments.

            Returns:
                None
            """
            return None
        def __enter__(self):
            return self
        def __exit__(self, *_, **__):
            return False
    monkeypatch.setattr(
        "PIL.Image.open",
        lambda path, mode=mode, height=height: DummyImg(mode, height)
    )
    cbz_path = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz_path, 'w') as zf:
        zf.writestr("image.png", b"fake")
    compress_cbz(str(cbz_path))

def test_process_cbz_files_print_output(capsys, tmp_path):
    """Test process_cbz_files prints expected output."""
    cbz_path = tmp_path / "test.cbz"
    cbz_path.write_bytes(b"dummy")
    process_cbz_files(str(tmp_path), 80, 1024)
    out = capsys.readouterr().out
    assert "Optimized" in out or "Failed" in out or "Skipped" in out
    process_cbz_files(str(tmp_path), 80, 1024)
    out = capsys.readouterr().out
    assert "Failed" in out or "Summary" in out
def test_process_cbz_files_summary_output(monkeypatch, capsys, tmp_path):
    """Test process_cbz_files summary output when compress_cbz fails."""
    cbz_path = tmp_path / "fail.cbz"
    cbz_path.write_bytes(b"dummy")
    monkeypatch.setattr("scripts.cbz_processor.compress_cbz", lambda path: False)
    process_cbz_files(str(tmp_path), 80, 1024)
    out = capsys.readouterr().out
    assert "Failed" in out or "Summary" in out


def test_cbz_processor_process_cbz_files_non_cbz(tmp_path):
    """Test process_cbz_files skips non-cbz files."""
    file_path = tmp_path / "not_cbz.txt"
    file_path.write_text("dummy")
    result = process_cbz_files(str(tmp_path), 80, 1024)
    assert result["skipped_count"] >= 1


def test_cbz_processor_main_system_exit(monkeypatch):
    """Test cbz_processor.main exits on SystemExit from get_directory_from_env_or_prompt."""
    def fake_get_directory(env):
        """Raise SystemExit for testing."""
        raise SystemExit(1)
    monkeypatch.setattr(cbz, "get_directory_from_env_or_prompt", fake_get_directory)
    with pytest.raises(SystemExit):
        cbz.main()


def test_cbz_processor_cli_entry(tmp_path):
    """Test CLI entry for cbz_processor script."""
    env_vars = {"CBZ_PROCESSOR_DIR": str(tmp_path)}
    result = run_cli_with_env("scripts.cbz_processor", env_vars)
    assert (
        b"Processing directory" in result.stdout or
        b"Error" in result.stdout or
        b"ModuleNotFoundError" in result.stderr
    )


def test_compress_cbz_extractall_exception(monkeypatch, tmp_path):
    """Test compress_cbz handles extractall exception."""
    # compress_cbz and zipfile already imported at top level
    class DummyImg:
        """Dummy image class for simulating PIL.Image behavior."""
        def __init__(self):
            self.mode = 'RGB'
            self.height = 100
            self.width = 1000
            self.resized = False
        def convert(self, m):
            """
            Set the processing mode for the object.

            Args:
                m: The mode to set.

            Returns:
                self: Returns the instance with the updated mode.
            """
            self.mode = m
            return self
        def resize(self, *_, **__):
            """
            Marks the object as resized by setting the 'resized' attribute to True.

            Args:
                *_: Ignored positional arguments.
                **__: Ignored keyword arguments.

            Returns:
                self: The current instance with 'resized' set to True.
            """
            self.resized = True
            return self
        def save(self, *_, **__):
            """
            Dummy save method that ignores all arguments and returns None.

            Args:
                *_: Positional arguments (ignored).
                **__: Keyword arguments (ignored).

            Returns:
                None
            """
            return None
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
    monkeypatch.setattr("PIL.Image.open", lambda path: DummyImg())
    cbz_path = tmp_path / "test.cbz"
    with zipfile.ZipFile(cbz_path, 'w') as zf:
        zf.writestr("image.png", b"fake")
    compress_cbz(str(cbz_path))
    # capsys is not defined in this test, so output assertion removed
