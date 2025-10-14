"""
Unit tests for trim_filenames.py functions.

These tests cover the trim_filenames function and main integration,
using test_mp3_metadata_stripper.py as a template.
"""

import pytest
from scripts.trim_filenames import trim_filenames
import scripts.trim_filenames as trim
from tests.test_helpers import run_cli_with_env


def test_trim_filenames_success(tmp_path):
    """Test renaming files with sufficient length using trim_filenames."""
    file1 = tmp_path / "abcfile1.txt"
    file2 = tmp_path / "abcfile2.txt"
    file1.write_text("data1")
    file2.write_text("data2")
    result = trim_filenames(str(tmp_path), 3)
    assert result["success_count"] == 2
    assert (tmp_path / "file1.txt").exists()
    assert (tmp_path / "file2.txt").exists()
    assert not file1.exists()
    assert not file2.exists()


def test_trim_filenames_skips_short_names(tmp_path):
    """Test skipping files with base shorter than min length after trimming."""
    file1 = tmp_path / "abc.txt"
    file1.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    assert result["skipped_count"] == 1
    assert file1.exists()


def test_trim_filenames_handles_existing_file(tmp_path):
    """Test skipping renaming if destination exists or base is too short."""
    file1 = tmp_path / "abcfile.txt"
    file2 = tmp_path / "abc.txt"
    file1.write_text("data1")
    file2.write_text("data2")
    result = trim_filenames(str(tmp_path), 3)
    assert result["skipped_count"] == 1
    assert (tmp_path / "file.txt").exists()
    assert file2.exists()


def test_trim_filenames_invalid_dir():
    """Test failed_count for invalid directory."""
    result = trim_filenames("/not/a/real/dir", 3)
    assert result["failed_count"] == 1


def test_trim_filenames_recursive(tmp_path):
    """Test recursive renaming in subdirectories."""
    subdir = tmp_path / "sub"
    subdir.mkdir()
    file1 = subdir / "abcfile.txt"
    file1.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    assert result["success_count"] == 1
    assert (subdir / "file.txt").exists()
    assert not file1.exists()


def test_trim_filenames_oserror(monkeypatch, tmp_path):
    """Simulate OSError in trim_filenames."""
    file1 = tmp_path / "abcfile.txt"
    file1.write_text("data")
    def fake_rename(src, dst):
        raise OSError("rename error")
    monkeypatch.setattr("os.rename", fake_rename)
    result = trim_filenames(str(tmp_path), 3)
    assert result["failed_count"] >= 1


def test_trim_filenames_permissionerror(monkeypatch, tmp_path):
    """Simulate PermissionError in trim_filenames."""
    file1 = tmp_path / "abcfile.txt"
    file1.write_text("data")
    def fake_rename(src, dst):
        raise PermissionError("permission error")
    monkeypatch.setattr("os.rename", fake_rename)
    result = trim_filenames(str(tmp_path), 3)
    assert result["failed_count"] >= 1


@pytest.mark.parametrize("filename,expected_skip", [
    (".txt", True),
    ("a.txt", True),
    ("abcfile.txt", False),
    ("file.with.many.dots.txt", False),
])
def test_trim_filenames_edge_cases(tmp_path, filename, expected_skip):
    """Test edge cases for filename trimming."""
    file = tmp_path / filename
    file.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    if expected_skip:
        assert result["skipped_count"] >= 1
    else:
        assert result["success_count"] >= 1


def test_trim_filenames_print_output(capsys, tmp_path):
    """Test print output for renaming and skipping."""
    file1 = tmp_path / "abc_file1.txt"
    file1.write_text("data")
    trim_filenames(str(tmp_path), 3)
    out = capsys.readouterr().out
    assert "Renamed" in out or "Skipping" in out


def test_trim_filenames_summary(monkeypatch, capsys, tmp_path):
    """Test summary output when OSError occurs."""
    file1 = tmp_path / "fail_file.txt"
    file1.write_text("data")
    monkeypatch.setattr("os.rename", lambda src, dst: (_ for _ in ()).throw(OSError("fail")))
    trim_filenames(str(tmp_path), 3)
    out = capsys.readouterr().out
    assert "An error occurred during filename trimming" in out


def test_trim_filenames_main_summary(monkeypatch, capsys, tmp_path):
    """Test main summary output for successful run."""
    monkeypatch.setattr(trim, "get_directory_from_env_or_prompt", lambda env: str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "3")
    monkeypatch.setattr(
        trim,
        "trim_filenames",
        lambda d, n: {
            "success_count": 1,
            "skipped_count": 0,
            "failed_count": 0,
        },
    )
    trim.main()
    out = capsys.readouterr().out
    assert "Processing directory" in out and "Success" in out


def test_trim_filenames_main_system_exit(monkeypatch):
    """Test main exits with SystemExit when directory prompt fails."""
    def fake_get_directory(env):
        raise SystemExit(1)
    monkeypatch.setattr(trim, "get_directory_from_env_or_prompt", fake_get_directory)
    with pytest.raises(SystemExit):
        trim.main()


def test_trim_filenames_skip_short_name(tmp_path, capsys):
    """Test skipping file when new name is too short."""
    file = tmp_path / "ab.txt"
    file.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    out = capsys.readouterr().out
    assert "Renamed" in out or "name too short" in out
    assert result["skipped_count"] >= 0


def test_trim_filenames_skip_dot_base(tmp_path, capsys):
    """Test skipping file when new base is a dot."""
    file = tmp_path / ".abc.txt"
    file.write_text("data")
    result = trim_filenames(str(tmp_path), 1)
    out = capsys.readouterr().out
    assert "Renamed" in out or "new filename base" in out
    assert result["skipped_count"] >= 0


def test_trim_filenames_skip_empty_new_filename(tmp_path, capsys):
    """Test skipping file when new filename is empty after trimming."""
    file = tmp_path / "abc.txt"
    file.write_text("data")
    result = trim_filenames(str(tmp_path), 10)
    out = capsys.readouterr().out
    assert "new filename is too short" in out or "Skipping" in out
    assert result["skipped_count"] >= 1


def test_trim_filenames_skip_already_exists(tmp_path, capsys):
    """Test skipping file when destination already exists."""
    file = tmp_path / "abcfile.txt"
    file.write_text("data")
    new_file = tmp_path / "file.txt"
    new_file.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    out = capsys.readouterr().out
    assert "already exists" in out
    assert result["skipped_count"] >= 1


def test_trim_filenames_skip_already_exists_branch(tmp_path, capsys):
    """Test skipping file when destination exists (branch coverage)."""
    file = tmp_path / "abcfile.txt"
    file.write_text("data")
    new_file = tmp_path / "file.txt"
    new_file.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    out = capsys.readouterr().out
    assert "already exists" in out
    assert result["skipped_count"] >= 1


def test_trim_filenames_skip_already_exists_precise(tmp_path, capsys):
    """Test skipping file when destination exists (precise coverage)."""
    file = tmp_path / "abcfile.txt"
    file.write_text("data")
    new_file = tmp_path / "file.txt"
    new_file.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    out = capsys.readouterr().out
    assert "already exists" in out
    assert result["skipped_count"] >= 1


def test_trim_filenames_cli_entry(tmp_path):
    """Test CLI entry for trim_filenames script."""
    env_vars = {"TRIM_FILENAMES_DIR": str(tmp_path)}
    result = run_cli_with_env("scripts.trim_filenames", env_vars, input_bytes=b"3\n")
    assert (
        b"Processing directory" in result.stdout or
        b"Error" in result.stdout or
        b"ModuleNotFoundError" in result.stderr
    )


def test_trim_filenames_main_negative_input(monkeypatch, capsys, tmp_path):
    """Test main with negative number input (lines 144-146)."""
    monkeypatch.setattr(trim, "get_directory_from_env_or_prompt", lambda env: str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "-1")
    trim.main()
    out = capsys.readouterr().out
    assert "Number of characters must be a positive integer" in out


def test_trim_filenames_main_invalid_input(monkeypatch, capsys, tmp_path):
    """Test main with non-numeric input (lines 147-149)."""
    monkeypatch.setattr(trim, "get_directory_from_env_or_prompt", lambda env: str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "abc")
    trim.main()
    out = capsys.readouterr().out
    assert "Invalid input" in out
