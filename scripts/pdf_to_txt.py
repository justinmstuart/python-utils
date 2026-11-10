"""
PDF to TXT Utility

Recursively scans a directory for PDF files, extracts text from each PDF,
and writes a plain text file alongside the source PDF.

Features:
    - Recursive processing of directories and subdirectories
    - Layout-aware text extraction using pdfplumber
    - Writes "<pdf_name>.txt" next to each source PDF
    - Pages are separated by a blank line in the output text
    - Prints a summary of processed, skipped, and failed files

Environment Variables:
    PDF_TO_TXT_DIR (optional): Directory path to process files in
"""

import os

import pdfplumber
from dotenv import load_dotenv

from scripts.utils import get_directory_from_env_or_prompt, make_summary_dict, print_result

TITLES = {
    "success": "Successfully converted",
    "warning": "Skipped file",
    "failed": "Failed to convert",
}

def extract_page_text(page):
    """Extract text from a single PDF page, preserving layout where possible."""
    try:
        text = page.extract_text(layout=True)
    except Exception:
        text = page.extract_text()
    if not text:
        return ""
    return "\n".join(line.rstrip() for line in text.splitlines())

def extract_text_from_pdf(pdf_path):
    """Extract text from every page of a PDF, joined by blank lines."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(extract_page_text(page) or "")
    return "\n\n".join(pages)

def convert_pdf_to_txt(pdf_path):
    """Convert a PDF to a plain text file next to the source and return the path."""
    text = extract_text_from_pdf(pdf_path)
    txt_path = f"{os.path.splitext(pdf_path)[0]}.txt"
    with open(txt_path, "w", encoding="utf-8") as file:
        file.write(text)
    return txt_path

def process_pdf_files(directory):
    """Recursively process PDF files in a directory and return summary stats."""
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if not filename.lower().endswith(".pdf"):
                skipped_count += 1
                continue

            try:
                convert_pdf_to_txt(file_path)
                print(f"✅ Converted: {file_path}")
                success_count += 1
            except Exception as error:
                print(f"🛑 Failed to convert {file_path}: {error}")
                failed_count += 1

    return make_summary_dict(success_count, skipped_count, failed_count)

def main():
    """Entry point for recursively converting PDFs to plain text files."""
    load_dotenv()
    directory = get_directory_from_env_or_prompt("PDF_TO_TXT_DIR")
    print(f"Processing directory: {directory}")
    result = process_pdf_files(directory)
    print_result(result, TITLES)

if __name__ == "__main__":
    main()
