#!/usr/bin/env python3

import os
import sys

def truncate_filenames(directory):
    """
    Recursively truncate the first 3 characters from all filenames in the specified directory
    and its subdirectories.
    """
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return False

    success = True
    try:
        # Walk through all directories and subdirectories
        for root, _, files in os.walk(directory):
            for filename in files:
                # Skip files with names shorter than 3 characters
                if len(filename) <= 3:
                    print(f"Skipping {os.path.join(root, filename)}: name too short")
                    continue

                # Create new filename without first 3 characters
                new_filename = filename[3:]

                # Full paths for rename operation
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)

                # Check if destination already exists
                if os.path.exists(new_path):
                    print(f"Skipping {old_path}: {new_filename} already exists")
                    continue

                # Rename the file
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} → {new_path}")

        return success
    except Exception as e:
        print(f"Error processing directory {directory}: {e}")
        return False

def main():
    # Prompt user for directory path
    directory = input("Enter the directory path: ").strip()

    if truncate_filenames(directory):
        print("File renaming completed successfully")
    else:
        print("File renaming failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
