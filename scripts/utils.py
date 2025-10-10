import os
def make_summary_dict(success_count, skipped_count, failed_count):
    """
    Return a summary dictionary for processed files.
    """
    return {
        "success_count": success_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count
    }

def print_newline():
    """
    Print a newline character to standard output.

    This function calls the print() function without arguments,
    which results in only a newline character being printed.

    Returns:
        None
    """
    print()

def print_result(stats, titles):
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
    print_newline()
    print("Processing complete. 🥳")
    print_newline()
    print("-" * 40)
    print(f"✅ {titles['success']} {stats['success_count']}")
    print(f"⚠️ {titles['warning']} {stats['skipped_count']}")
    print(f"🛑 {titles['failed']} {stats['failed_count']}")
    print_newline()

def get_directory_from_env_or_prompt(env_var, prompt_msg="Enter the directory path: "):
    """
    Get a directory path from an environment variable or prompt the user.

    Args:
        env_var (str): Name of the environment variable to check.
        prompt_msg (str): Prompt message for user input if env var is not set.

    Returns:
        str: The directory path provided by the environment or user.
    """
    directory = os.getenv(env_var)
    if not directory:
        directory = input(prompt_msg).strip()
    return directory

def get_positive_integer_input(prompt_msg="Enter a positive integer: "):
    """
    Prompt the user for a positive integer, with validation and error messages.

    Args:
        prompt_msg (str): The prompt message to display.

    Returns:
        int: The positive integer entered by the user.
    """
    while True:
        try:
            value = int(input(prompt_msg).strip())
            if value <= 0:
                print("\U0001F522 Please enter a positive number.")
                continue
            return value
        except ValueError:
            print("\U0001F6D1 Please enter a valid number.")
