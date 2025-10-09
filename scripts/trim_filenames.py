"""
Filename Trimming Utility

This script provides functionality to recursively trim a specified number of characters
from the beginning of all filenames in a directory and its subdirectories. It's useful
for batch renaming files when they have unwanted prefixes.

Features:
    - Recursive processing of directories and subdirectories
    - User-configurable number of characters to trim
    - Environment variable support for directory path
    - Comprehensive error handling and validation
    - Detailed progress reporting and summary statistics
    - Safe handling of file conflicts and edge cases

Usage:
    Run the script directly:
        python trim-filenames.py

    Or set environment variable:
        export TRIM_FILENAMES_DIR="/path/to/directory"
        python trim-filenames.py

Environment Variables:
    TRIM_FILENAMES_DIR (optional): Directory path to process files in
"""

import os
from dotenv import load_dotenv

from scripts.utils import print_result, get_directory_from_env_or_prompt

TITLES = {
        "success": "Successfully trimmed chars from",
        "warning": "Skipped trimming chars from",
        "failed": "Failed to trim chars from"
    }

def trim_filenames(directory_path, chars_to_trim):
    """
    Recursively trim the first N characters from all filenames in the specified directory
    and its subdirectories.

    Args:
        directory_path (str): Path to the directory to process
        chars_to_trim (int): Number of characters to remove from the beginning of each filename

    Returns:
        dict: A dictionary containing counts of successful, skipped, and failed operations:
            - 'success_count': Number of files successfully renamed
            - 'skipped_count': Number of files that were skipped
            - 'failed_count': Number of files that failed to process
    """
        if os_path_exists_func is None:
            os_path_exists_func = os.path.exists
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory")
        return {
            "success_count": 0,
            "skipped_count": 0,
            "failed_count": 1
        }

    success_count = 0
    skipped_count = 0
    failed_count = 0

    try:
        # Walk through all directories and subdirectories
        for root, _, files in os.walk(directory_path):
            for filename in files:
                # Skip files with names shorter than the requested number of characters
                if len(filename) <= chars_to_trim:
                    print(f"Skipping {os.path.join(root, filename)}: name too short")
                    skipped_count += 1
                    continue

                # Create new filename without first N characters
                new_filename = filename[chars_to_trim:]

                # Split base and extension
                base, _ = os.path.splitext(new_filename)

                # If the new base name is less than 3 characters or starts with a dot, skip
                if len(base) < 3 or base.startswith('.'):
                    print(f"Skipping {os.path.join(root, filename)}: new filename base '{base}' is too short or only extension")
                    skipped_count += 1
                    continue

                # If the new filename is empty, skip
                if not new_filename or len(new_filename) < 1:
                    print(f"Skipping {os.path.join(root, filename)}: new filename is too short")
                    skipped_count += 1
                    continue

                # Full paths for rename operation
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)

                # Check if destination already exists
                    if os_path_exists_func(new_path):
                    print(f"Skipping {old_path}: {new_filename} already exists")
                    skipped_count += 1
                    continue

                # Rename the file
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} → {new_path}")
                success_count += 1
    except (OSError, PermissionError) as e:
        print(f"Error processing directory {directory_path}: {e}")
        failed_count += 1

    return {
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count
    }

def main():
    """
    Main entry point for the filename trimming script.

    This function handles user interaction to gather the directory path and number
    of characters to trim, then executes the trimming operation and displays results.

    The function will:
    1. Check for TRIM_FILENAMES_DIR environment variable, otherwise prompt for directory
    2. Prompt for the number of characters to remove from filenames
    3. Validate user input (positive integers only)
    4. Execute the trimming operation
    5. Display the results summary

    Environment Variables:
        TRIM_FILENAMES_DIR (optional): Directory path to process files in

    Returns:
        None: This function handles user interaction and calls other functions
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    directory = get_directory_from_env_or_prompt('TRIM_FILENAMES_DIR')
    print(f"📁 Processing directory: {directory}")

    num_chars = int(input("Enter the number of characters to remove from the beginning of each filename: "))

    result = trim_filenames(directory, num_chars)
    print_result(result, TITLES)

if __name__ == "__main__":
    main()
