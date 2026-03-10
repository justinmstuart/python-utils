"""
CBZ Cleanup Utility

Recursively scans a directory and removes backup CBZ files that end with
"_original.cbz" (extension matching is case-insensitive).

Features:
    - Recursive processing of directories and subdirectories
    - Deletes only files ending in "_original.cbz"
    - Reads target directory from .env via CBZ_PROCESSOR_DIR
    - Continues processing when a delete operation fails
    - Prints a summary of deleted, skipped, and failed files

Usage:
    python -m scripts.cbz_clean_up

Environment Variables:
    CBZ_PROCESSOR_DIR (optional): Directory path to process files in
"""

import os

from dotenv import load_dotenv

from scripts.utils import get_directory_from_env_or_prompt, make_summary_dict, print_result

TITLES = {
    "success": "Successfully deleted",
    "warning": "Skipped file",
    "failed": "Failed to delete",
}


def _is_original_cbz(filename):
    """Return True when filename ends with the exact '_original.cbz' pattern."""
    base, extension = os.path.splitext(filename)
    return extension.lower() == ".cbz" and base.endswith("_original")


def clean_up_original_cbz_files(directory):
    """
    Recursively delete files matching the '_original.cbz' naming pattern.

    Args:
        directory (str): Root directory to scan.

    Returns:
        dict: Summary counts for successful, skipped, and failed operations.
    """
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if not _is_original_cbz(filename):
                skipped_count += 1
                continue

            try:
                os.remove(filepath)
                print(f"Deleted: {filepath}")
                success_count += 1
            except OSError as error:
                print(f"Failed to delete {filepath}: {error}")
                failed_count += 1

    return make_summary_dict(success_count, skipped_count, failed_count)


def main():
    """Entry point for recursive cleanup of '_original.cbz' backup files."""
    load_dotenv()
    directory = get_directory_from_env_or_prompt("CBZ_PROCESSOR_DIR")
    print(f"Processing directory: {directory}")
    result = clean_up_original_cbz_files(directory)
    print_result(result, TITLES)


if __name__ == "__main__":
    main()
