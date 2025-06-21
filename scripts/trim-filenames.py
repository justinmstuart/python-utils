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

def print_result(stats):
    """
    Print the summary of the filename trimming process results.

    Args:
        stats (dict): A dictionary containing the counts of processed files.
            Expected keys:
            - 'success_count': Number of files successfully renamed
            - 'skipped_count': Number of files that were skipped
            - 'failed_count': Number of files that failed to process

    Returns:
        None: This function prints results to console only.
    """
    print()
    print("Processing complete. 🥳")
    print()
    print("-" * 40)
    print(f"✅ Successfully trim chars from {stats['success_count']} filenames.")
    print(f"⚠️ Skipped trimming chars from {stats['skipped_count']} filenames.")
    print(f"🛑 Failed to trim chars from  {stats['failed_count']} filenames.")
    print("-" * 40)
    print()

def print_newline():
    """
    Print a newline character to standard output.

    This function calls the print() function without arguments,
    which results in only a newline character being printed.

    Returns:
        None
    """
    print()

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

                # Full paths for rename operation
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)

                # Check if destination already exists
                if os.path.exists(new_path):
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

    # Get the target directory from the user
    directory = os.getenv('TRIM_FILENAMES_DIR')
    if not directory:
        directory = input("Enter the directory path: ").strip()

    print(f"📁 Processing directory: {directory}")

    # Prompt user for number of characters to remove
    while True:
        try:
            num_chars = int(input("Enter the number of characters to remove from the beginning of each filename: ").strip())
            if num_chars <= 0:
                print("🔢 Please enter a positive number.")
                continue
            break
        except ValueError:
            print("🛑 Please enter a valid number.")

    result = trim_filenames(directory, num_chars)
    print_result(result)

if __name__ == "__main__":
    main()
