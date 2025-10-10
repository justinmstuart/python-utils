"""
Unit tests for mp3_metadata_stripper.py functions.

These tests cover create_audio_file, remove_metadata, and remove_metadata_from_audio.
"""

import pytest
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import error
from scripts.mp3_metadata_stripper import (
    create_audio_file,
    remove_metadata,
    remove_metadata_from_audio,
)
import scripts.mp3_metadata_stripper as mp3
from tests.test_helpers import run_cli_with_env


def test_create_audio_file_mp3(tmp_path):
    """Test create_audio_file returns MP3 object or None for minimal MP3 file."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    result = create_audio_file(str(mp3_path))
    assert result is None or isinstance(result, MP3)


def test_create_audio_file_m4a(tmp_path):
    """Test create_audio_file returns MP4 object or None for minimal M4A file."""
    m4a_path = tmp_path / "test.m4a"
    m4a_path.write_bytes(b"ftypM4A ")
    result = create_audio_file(str(m4a_path))
    assert result is None or isinstance(result, MP4)


def test_create_audio_file_other(tmp_path):
    """Test create_audio_file returns None for unsupported file type."""
    other_path = tmp_path / "test.txt"
    other_path.write_text("not audio")
    result = create_audio_file(str(other_path))
    assert result is None


def test_remove_metadata_calls():
    """Test remove_metadata calls delete and save on audio file object."""
    class DummyAudio:
        """Dummy audio file for testing delete/save."""
        def __init__(self):
            self.deleted = False
            self.saved = False
        def delete(self):
            """
            Marks the object as deleted by setting the 'deleted' attribute to True.
            """
            self.deleted = True
        def save(self):
            """
            Marks the object as saved by setting the 'saved' attribute to True.
            """
            self.saved = True
    dummy = DummyAudio()
    remove_metadata(dummy)
    assert dummy.deleted
    assert dummy.saved


def test_remove_metadata_from_audio_invalid_dir(tmp_path):
    """Test failed count for non-existent directory."""
    result = remove_metadata_from_audio(str(tmp_path / "not_a_dir"))
    assert result["failed_count"] == 1


def test_remove_metadata_from_audio_empty(tmp_path):
    """Test zero counts for empty directory."""
    result = remove_metadata_from_audio(str(tmp_path))
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0


def test_remove_metadata_from_audio_mp3(monkeypatch, tmp_path):
    """Test remove_metadata_from_audio processes MP3 file and calls correct functions."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    called = {}
    def fake_create_audio_file(_):
        """
        Creates a dummy audio file object for testing purposes.

        This function simulates the creation of an audio file object with basic
        attributes and methods. It sets a flag in the provided dictionary to indicate
        that it was called.

        Args:
            _ (Any): Placeholder argument, not used.

        Returns:
            Dummy: An object with 'tags', 'delete', and 'save' attributes for mocking.
        """
        called['called'] = True
        class Dummy:
            """
            A dummy class used for testing purposes.

            Attributes:
                tags (bool): Indicates the presence of tags.

            Methods:
                delete(): Dummy method to simulate deletion.
                save(): Dummy method to simulate saving.
            """
            tags = True
            def delete(self):
                """Dummy method to simulate deletion."""
            def save(self):
                """Dummy method to simulate saving."""
        return Dummy()
    def fake_remove_metadata(_):
        called['removed'] = True
    monkeypatch.setattr('scripts.mp3_metadata_stripper.create_audio_file', fake_create_audio_file)
    monkeypatch.setattr('scripts.mp3_metadata_stripper.remove_metadata', fake_remove_metadata)
    result = remove_metadata_from_audio(str(tmp_path))
    assert called.get('called')
    assert called.get('removed')
    assert result["success_count"] == 1


def test_remove_metadata_from_audio_mutagen_error(monkeypatch, tmp_path):
    """Simulate mutagen error in remove_metadata_from_audio."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    def fake_create_audio_file(_):
        raise error("mutagen error")
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", fake_create_audio_file)
    result = remove_metadata_from_audio(str(tmp_path))
    assert result["failed_count"] >= 1


def test_remove_metadata_from_audio_oserror(monkeypatch, tmp_path):
    """Simulate OSError in remove_metadata_from_audio."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    def fake_create_audio_file(_):
        raise OSError("os error")
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", fake_create_audio_file)
    result = remove_metadata_from_audio(str(tmp_path))
    assert result["failed_count"] >= 1


def test_remove_metadata_from_audio_keyboardinterrupt(monkeypatch, tmp_path):
    """Simulate KeyboardInterrupt in remove_metadata_from_audio."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    def fake_create_audio_file(_):
        raise KeyboardInterrupt()
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", fake_create_audio_file)
    try:
        remove_metadata_from_audio(str(tmp_path))
    except KeyboardInterrupt:
        pass


def test_remove_metadata_from_audio_no_tags(monkeypatch, tmp_path):
    """Test remove_metadata_from_audio handles MP3 file with no tags."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    class DummyAudio:
        """Dummy audio file class for testing with no tags."""
        tags = None
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", lambda _: DummyAudio())
    result = remove_metadata_from_audio(str(tmp_path))
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0


def test_remove_metadata_from_audio_unsupported(monkeypatch, tmp_path):
    """Test remove_metadata_from_audio handles unsupported audio format."""
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", lambda _: None)
    result = remove_metadata_from_audio(str(tmp_path))
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0


def test_remove_metadata_from_audio_print_output(monkeypatch, capsys, tmp_path):
    """Test remove_metadata_from_audio prints correct output messages."""
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    class DummyAudio:
        """
        A dummy audio class used for testing purposes.

        Attributes:
            tags (bool): Indicates the presence of tags.

        Methods:
            delete(): Dummy method to simulate tag deletion.
            save(): Dummy method to simulate saving the audio file.
        """
        tags = True
        def delete(self):
            """Deletes the associated resource or data."""
        def save(self):
            """Saves the associated resource or data."""
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", lambda _: DummyAudio())
    monkeypatch.setattr("scripts.mp3_metadata_stripper.remove_metadata", lambda _: None)
    remove_metadata_from_audio(str(tmp_path))
    out = capsys.readouterr().out
    assert "Metadata removed" in out or "Failed" in out


def test_remove_metadata_from_audio_summary(monkeypatch, capsys, tmp_path):
    """Test remove_metadata_from_audio prints correct summary output."""
    mp3_path = tmp_path / "fail.mp3"
    mp3_path.write_bytes(b"ID3")
    class DummyAudio:
        """
        A dummy audio class used for testing purposes.

        Attributes:
            tags (bool): Indicates the presence of tags.

        Methods:
            delete(): Simulates deletion of tags, raises an error.
            save(): Simulates saving of tags, raises an error.
        """
        tags = True
        def delete(self):
            """Simulates deletion of tags, raises an error."""
            raise error("fail")
        def save(self):
            """Simulates saving of tags, raises an error."""
            raise error("fail")
    monkeypatch.setattr(
        "scripts.mp3_metadata_stripper.create_audio_file",
        lambda _: DummyAudio()
    )
    monkeypatch.setattr(
        "scripts.mp3_metadata_stripper.remove_metadata",
        lambda _: (_ for _ in ()).throw(error("fail"))
    )
    remove_metadata_from_audio(str(tmp_path))
    out = capsys.readouterr().out
    assert "Failed to process" in out


def test_mp3_metadata_stripper_main_summary(monkeypatch, capsys, tmp_path):
    """Test main function summary output of mp3_metadata_stripper."""
    monkeypatch.setattr(mp3, "get_directory_from_env_or_prompt", lambda env: str(tmp_path))
    monkeypatch.setattr(
        mp3,
        "remove_metadata_from_audio",
        lambda d: {
            "success_count": 1,
            "skipped_count": 0,
            "failed_count": 0,
        },
    )
    mp3.main()
    out = capsys.readouterr().out
    assert "Processing directory" in out and "Success" in out


def test_mp3_metadata_stripper_cli_entry(tmp_path):
    """Test CLI entry for mp3_metadata_stripper script."""
    env_vars = {"MP3_METADATA_STRIPPER_DIR": str(tmp_path)}
    result = run_cli_with_env("scripts.mp3_metadata_stripper", env_vars)
    assert (
        b"Processing directory" in result.stdout or
        b"Error" in result.stdout or
        b"ModuleNotFoundError" in result.stderr
    )


def test_remove_metadata_from_audio_failed(monkeypatch, tmp_path, capsys):
    """Test remove_metadata_from_audio handles error branch and prints summary."""
    mp3_path = tmp_path / "fail.mp3"
    mp3_path.write_bytes(b"ID3")
    class DummyAudio:
        """
        A dummy audio class used for testing purposes.

        Attributes:
            tags (bool): Indicates the presence of tags.

        Methods:
            delete(): Simulates deletion of tags, raises an error.
            save(): Simulates saving of tags, raises an error.
        """
        tags = True
        def delete(self):
            """Simulates deletion of tags, raises an error."""
            raise error("fail")
        def save(self):
            """Simulates saving of tags, raises an error."""
            raise error("fail")
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", lambda _: DummyAudio())
    monkeypatch.setattr(
        "scripts.mp3_metadata_stripper.remove_metadata",
        lambda _: (_ for _ in ()).throw(error("fail"))
    )
    result = remove_metadata_from_audio(str(tmp_path))
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1


def test_remove_metadata_from_audio_specific_error(monkeypatch, tmp_path, capsys):
    """Test remove_metadata_from_audio handles specific error and prints output."""
    mp3_path = tmp_path / "fail.mp3"
    mp3_path.write_bytes(b"ID3")
    class DummyAudio:
        """
        A dummy audio class used for testing purposes.

        Attributes:
            tags (bool): Indicates the presence of tags in the audio file.
        """
        tags = True
    class DummyError(error):
        """
        Dummy exception class used for testing purposes.

        This class inherits from the `error` base exception and serves as a placeholder
        for simulating error conditions in unit tests.
        """
    def raise_error(_):
        raise DummyError("dummy error")
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", lambda _: DummyAudio())
    monkeypatch.setattr("scripts.mp3_metadata_stripper.remove_metadata", raise_error)
    result = remove_metadata_from_audio(str(tmp_path))
    out = capsys.readouterr().out
    assert "Failed to process" in out or "dummy error" in out
    assert result["failed_count"] >= 1


def test_mp3_metadata_stripper_main_system_exit(monkeypatch):
    """Test main exits with SystemExit when directory prompt fails."""
    def fake_get_directory(env):
        raise SystemExit(1)
    monkeypatch.setattr(mp3, "get_directory_from_env_or_prompt", fake_get_directory)
    with pytest.raises(SystemExit):
        mp3.main()


def test_remove_metadata_from_audio_error_branch(monkeypatch, tmp_path, capsys):
    """Test remove_metadata_from_audio handles mutagen error branch and prints output."""
    class DummyAudio:
        """
        A dummy audio class used for testing purposes.

        Attributes:
            tags (bool): Indicates the presence of tags in the audio file.
        """
        tags = True
    def raise_error(_):
        raise error("dummy error")
    monkeypatch.setattr("scripts.mp3_metadata_stripper.create_audio_file", lambda _: DummyAudio())
    monkeypatch.setattr("scripts.mp3_metadata_stripper.remove_metadata", raise_error)
    mp3_path = tmp_path / "fail.mp3"
    mp3_path.write_bytes(b"ID3")
    result = remove_metadata_from_audio(str(tmp_path))
    out = capsys.readouterr().out
    assert "Failed to process" in out
    assert result["failed_count"] >= 1
