"""
Unit tests for mp3_metadata_stripper.py functions.

These tests cover create_audio_file, remove_metadata, and remove_metadata_from_audio.
"""

from scripts.mp3_metadata_stripper import create_audio_file, remove_metadata, remove_metadata_from_audio

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4


def test_create_audio_file_mp3(tmp_path):
    """
    Test that create_audio_file returns an MP3 object or None for a minimal MP3 file.
    """
    # Create a dummy MP3 file
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")  # Write minimal MP3 header
    # Unable to mock MP3 file, expect None at this time.
    result = create_audio_file(str(mp3_path))
    assert result is None or isinstance(result, MP3)


def test_create_audio_file_m4a(tmp_path):
    """
    Test that create_audio_file returns an MP4 object or None for a minimal M4A file.
    """
    # Create a dummy M4A file
    m4a_path = tmp_path / "test.m4a"
    m4a_path.write_bytes(b"ftypM4A ")  # Write minimal M4A header
    result = create_audio_file(str(m4a_path))
    assert result is None or isinstance(result, MP4)


def test_create_audio_file_other(tmp_path):
    """
    Test that create_audio_file returns None for an unsupported file type.
    """
    # Create a dummy file with unknown extension
    other_path = tmp_path / "test.txt"
    other_path.write_text("not audio")
    result = create_audio_file(str(other_path))
    assert result is None


def test_remove_metadata_calls(monkeypatch):
    """
    Test that remove_metadata calls delete and save on the audio file object.
    """
    class DummyAudio:
        def __init__(self):
            self.deleted = False
            self.saved = False

        def delete(self):
            self.deleted = True

        def save(self):
            self.saved = True

    dummy = DummyAudio()
    remove_metadata(dummy)
    assert dummy.deleted
    assert dummy.saved


def test_remove_metadata_from_audio_invalid_dir(tmp_path):
    """
    Test that remove_metadata_from_audio returns a failed count for a non-existent directory.
    """
    # Pass a non-existent directory
    result = remove_metadata_from_audio(str(tmp_path / "not_a_dir"))
    assert result["failed_count"] == 1


def test_remove_metadata_from_audio_empty(tmp_path):
    """
    Test that remove_metadata_from_audio returns zero counts for an empty directory.
    """
    # Directory exists but has no files
    result = remove_metadata_from_audio(str(tmp_path))
    assert result["success_count"] == 0
    assert result["skipped_count"] == 0
    assert result["failed_count"] == 0


def test_remove_metadata_from_audio_mp3(monkeypatch, tmp_path):
    """
    Test that remove_metadata_from_audio processes an MP3 file and calls the correct functions.
    """
    # Create a dummy MP3 file and mock create_audio_file and remove_metadata
    mp3_path = tmp_path / "test.mp3"
    mp3_path.write_bytes(b"ID3")
    called = {}

    def fake_create_audio_file(path):
        called['called'] = True

        class Dummy:
            tags = True

            def delete(self): pass

            def save(self): pass

        return Dummy()

    def fake_remove_metadata(audio_file):
        called['removed'] = True

    monkeypatch.setattr('scripts.mp3_metadata_stripper.create_audio_file', fake_create_audio_file)
    monkeypatch.setattr('scripts.mp3_metadata_stripper.remove_metadata', fake_remove_metadata)
    result = remove_metadata_from_audio(str(tmp_path))
    assert called.get('called')
    assert called.get('removed')
    assert result["success_count"] == 1
