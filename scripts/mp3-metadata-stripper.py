"""
Audio Metadata Stripper

This script recursively removes metadata from MP3 and M4A files in a specified directory.
It traverses through all subdirectories to find and process all audio files.

Requirements:
    - Python 3.6+
    - mutagen library (pip install mutagen)

Example usage:
    python script.py
    # Then enter the directory path when prompted
"""

import os
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, error
from dotenv import load_dotenv

from utils import print_newline, print_result, get_directory_from_env_or_prompt

TITLES = {
    "success": "Successfully removed metadata from",
    "warning": "No metadata found in",
    "failed": "Failed to process"
}

def create_audio_file(file_path: str) -> MP3 | MP4 | None:
    """
    Creates an audio file object based on the file extension.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        MP3 | MP4: An instance of MP3 or MP4 class based on the file type.
    """
    if file_path.lower().endswith('.mp3'):
        return MP3(file_path, ID3=ID3)
    elif file_path.lower().endswith('.m4a'):
        return MP4(file_path)
    else:
        return None


def remove_metadata(audio_file: MP3 | MP4):
    """
    Remove all metadata from an audio file and save the changes.

    This function removes all metadata tags from the given audio file object
    and saves the changes back to the file on disk.

    Args:
        audio_file (MP3 | MP4): The audio file object from which to remove metadata.
                              Must be either an MP3 or MP4 object with delete() and save() methods.

    Returns:
        None
    """
    audio_file.delete()  # Remove all metadata
    audio_file.save()    # Save the file without metadata

def remove_metadata_from_audio(directory_path):
    """
    Recursively removes metadata from all MP3 and M4A files in the specified directory and its subdirectories.

    Args:
        directory_path (str): Path to the directory containing audio files.
            The path can be absolute or relative to the current working directory.

    Returns:
        dict: Statistics about processed files including counts of metadata removed,
              files without metadata, and failures.

    Notes:
        - This function uses os.walk to recursively traverse all subdirectories.
        - Files with '.mp3' and '.m4a' extensions (case-insensitive) will be processed.
        - Progress messages are printed to the console.
    """
    success_count = 0
    skipped_count = 0
    failed_count = 0

    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory.")
        return {
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": 1
        }

    # Recursively traverse the directory structure
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                audio_file = create_audio_file(file_path)

                if audio_file is not None and audio_file.tags:
                    remove_metadata(audio_file)
                    success_count += 1
                    print(f"Metadata removed from: {file_path}")
            except error as e:
                failed_count += 1
                print(f"Failed to process {file_path}: {e}")
            except OSError as e:
                failed_count += 1
                print(f"File system error processing {file_path}: {e}")
            except KeyboardInterrupt:
                print("Process interrupted by user.")
                raise
            except Exception as e:
                failed_count += 1
                print(f"Unexpected error processing {file_path}: {str(e)}")

    return {
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count
    }

def main():
    """
    Main entry point for the audio metadata stripper script.

    This function handles user interaction to gather the directory path,
    executes the metadata removal operation, and displays results.

    The function will:
    1. Load environment variables from .env file if it exists
    2. Check for MP3_METADATA_STRIPPER_DIR environment variable, otherwise prompt for directory
    3. Execute the metadata removal operation on all MP3 and M4A files
    4. Display progress messages and final results summary

    Environment Variables:
        MP3_METADATA_STRIPPER_DIR (optional): Directory path to process audio files in

    Returns:
        None: This function handles user interaction and calls other functions
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Get the target directory from the user
    directory = get_directory_from_env_or_prompt('MP3_METADATA_STRIPPER_DIR')
    print(f"📁 Processing directory: {directory}")

    print_newline()
    print("Starting to process audio files 🎵")
    print_newline()

    result = remove_metadata_from_audio(directory)
    print_result(result, TITLES)


if __name__ == "__main__":
    main()
