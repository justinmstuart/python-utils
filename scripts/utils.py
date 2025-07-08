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
    print(f"🛑 {titles['failed']}  {stats['failed_count']}")
    print("-" * 40)
    print_newline()
