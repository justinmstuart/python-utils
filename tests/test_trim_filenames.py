"""
Unit tests for trim_filenames.py functions.

These tests cover the trim_filenames function and main integration, using test_mp3_metadata_stripper.py as a template.
"""

from scripts.trim_filenames import trim_filenames
import os


def test_trim_filenames_success(tmp_path):
    """
    Test that trim_filenames successfully renames files with sufficient length.
    """
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
    """
    Test that trim_filenames skips files with names that result in a base shorter than 3 after trimming.
    """
    file1 = tmp_path / "abc.txt"  # base 'abc', after trimming 3: ''
    file1.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    assert result["skipped_count"] == 1
    assert file1.exists()


def test_trim_filenames_handles_existing_file(tmp_path):
    """
    Test that trim_filenames skips renaming if destination file already exists or new base is too short.
    """
    file1 = tmp_path / "abcfile.txt"  # after trimming: 'file.txt', base 'file'
    file2 = tmp_path / "abc.txt"      # after trimming: '.txt', base ''
    file1.write_text("data1")
    file2.write_text("data2")
    result = trim_filenames(str(tmp_path), 3)
    assert result["skipped_count"] == 1
    assert (tmp_path / "file.txt").exists()
    assert file2.exists()


def test_trim_filenames_invalid_dir():
    """
    Test that trim_filenames returns failed_count for invalid directory.
    """
    result = trim_filenames("/not/a/real/dir", 3)
    assert result["failed_count"] == 1


def test_trim_filenames_recursive(tmp_path):
    """
    Test that trim_filenames works recursively in subdirectories.
    """
    subdir = tmp_path / "sub"
    subdir.mkdir()
    file1 = subdir / "abcfile.txt"
    file1.write_text("data")
    result = trim_filenames(str(tmp_path), 3)
    assert result["success_count"] == 1
    assert (subdir / "file.txt").exists()
    assert not file1.exists()
