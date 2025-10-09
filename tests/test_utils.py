"""
Unit tests for scripts.utils module.

This file tests utility functions for printing newlines, printing results,
and getting directory paths from environment variables or user input.
"""

from unittest import mock
import pytest
from scripts.utils import get_directory_from_env_or_prompt, print_newline, print_result


def test_print_newline(capsys):
    """
    Test that print_newline prints exactly one newline character.
    """
    print_newline()
    captured = capsys.readouterr()
    assert captured.out == "\n"


def test_print_result(capsys):
    """
    Test that print_result prints the correct summary output for given stats and titles.
    """
    stats = {'success_count': 2, 'skipped_count': 1, 'failed_count': 0}
    titles = {
        'success': 'Processed',
        'warning': 'Skipped',
        'failed': 'Failed'
    }
    print_result(stats, titles)
    captured = capsys.readouterr()
    assert "Processed 2" in captured.out
    assert "Skipped 1" in captured.out
    assert "Failed 0" in captured.out


def test_get_directory_from_env(monkeypatch, tmp_path):
    """
    Test get_directory_from_env_or_prompt returns env variable if set.
    """
    monkeypatch.setenv("TRIM_FILENAMES_DIR", str(tmp_path))
    result = get_directory_from_env_or_prompt("TRIM_FILENAMES_DIR")
    assert result == str(tmp_path)


def test_get_directory_from_prompt(monkeypatch, tmp_path):
    """
    Test get_directory_from_env_or_prompt prompts user if env not set.
    """
    monkeypatch.delenv("TRIM_FILENAMES_DIR", raising=False)
    monkeypatch.setattr("builtins.input", lambda prompt: str(tmp_path))
    result = get_directory_from_env_or_prompt("TRIM_FILENAMES_DIR")
    assert result == str(tmp_path)


def test_print_result_and_newline(capsys):
    """
    Test print_result and print_newline output.
    """
    result = {"success_count": 1, "skipped_count": 2, "failed_count": 3}
    titles = {"success": "Success", "warning": "Warning", "failed": "Failed"}
    print_newline()
    print_result(result, titles)
    out = capsys.readouterr().out
    assert "Success" in out and "Warning" in out and "Failed" in out


def test_print_result_various(capsys):
    """
    Test print_result with various input combinations.
    """
    from scripts.utils import print_result
    result = {"success_count": 5, "skipped_count": 0, "failed_count": 0}
    titles = {"success": "Success", "warning": "Warning", "failed": "Failed"}
    print_result(result, titles)
    out = capsys.readouterr().out
    assert "Success" in out
    result = {"success_count": 0, "skipped_count": 5, "failed_count": 0}
    print_result(result, titles)
    out = capsys.readouterr().out
    assert "Warning" in out
    result = {"success_count": 0, "skipped_count": 0, "failed_count": 5}
    print_result(result, titles)
    out = capsys.readouterr().out
    assert "Failed" in out


def test_print_result_all_zero(capsys):
    """
    Test print_result when all counts are zero.
    """
    from scripts.utils import print_result
    result = {"success_count": 0, "skipped_count": 0, "failed_count": 0}
    titles = {"success": "Success", "warning": "Warning", "failed": "Failed"}
    print_result(result, titles)
    out = capsys.readouterr().out
    assert "Processing complete" in out


def test_get_positive_integer_input(monkeypatch, capsys):
    from scripts.utils import get_positive_integer_input
    inputs = iter(["-1", "abc", "0", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    result = get_positive_integer_input("Enter a number: ")
    out = capsys.readouterr().out
    assert result == 5
    assert "Please enter a positive number" in out
    assert "Please enter a valid number" in out
