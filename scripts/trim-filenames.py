import os
import sys

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

def trim_filenames(directory, num_chars):
    """
    Recursively trim the first N characters from all filenames in the specified directory
    and its subdirectories.

    Args:
        directory (str): Path to the directory to process
        num_chars (int): Number of characters to remove from the beginning of each filename

    Returns:
        dict: A dictionary containing counts of successful, skipped, and failed operations:
            - 'success_count': Number of files successfully renamed
            - 'skipped_count': Number of files that were skipped
            - 'failed_count': Number of files that failed to process
    """
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
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
        for root, _, files in os.walk(directory):
            for filename in files:
                # Skip files with names shorter than the requested number of characters
                if len(filename) <= num_chars:
                    print(f"Skipping {os.path.join(root, filename)}: name too short")
                    skipped_count += 1
                    continue

                # Create new filename without first N characters
                new_filename = filename[num_chars:]

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
        print(f"Error processing directory {directory}: {e}")
        failed_count += 1

    return {
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count
    }

def main():
    """
    Main function that prompts for user input and runs the filename trimming process.

    Gets the directory path and number of characters to trim from user input,
    validates the inputs, runs the trim_filenames function, and displays the results.
    """
    # Prompt user for directory path
    directory = input("Enter the directory path: ").strip()

    # Prompt user for number of characters to remove
    while True:
        try:
            num_chars = int(input("Enter the number of characters to remove from the beginning of each filename: ").strip())
            if num_chars <= 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    result = trim_filenames(directory, num_chars)
    print_result(result)

if __name__ == "__main__":
    main()
