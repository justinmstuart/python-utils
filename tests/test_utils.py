"""
Unit tests for scripts.utils module.

This file tests utility functions for printing newlines, printing results,
and getting directory paths from environment variables or user input.
"""

from unittest import mock
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


def test_get_directory_from_env(monkeypatch):
    """
    Test getting directory from environment variable.
    """
    monkeypatch.setenv('TEST_DIR', '/tmp/testdir')
    result = get_directory_from_env_or_prompt('TEST_DIR')
    assert result == '/tmp/testdir'


def test_get_directory_from_prompt(monkeypatch):
    """
    Test getting directory from user prompt when environment variable is not set.
    """
    monkeypatch.delenv('TEST_DIR', raising=False)
    with mock.patch('builtins.input', return_value='/tmp/promptdir'):
        result = get_directory_from_env_or_prompt('TEST_DIR')
    assert result == '/tmp/promptdir'
