"""
PDF to CBZ Utility

Recursively scans a directory for PDF files, converts each PDF into images,
packages the images into a CBZ archive, and then optimizes the resulting CBZ.

Features:
    - Recursive processing of directories and subdirectories
    - Converts each PDF page to images named "<pdf_name>_001.png", etc.
    - Stores generated images in a directory matching the PDF file name
    - Creates a .zip archive of that directory and renames it to .cbz
    - Runs CBZ optimization on the generated .cbz file
    - Prints a summary of processed, skipped, and failed files

Environment Variables:
    PDF_TO_CBZ_DIR (optional): Directory path to process files in
"""

import os
import re
import zipfile

from dotenv import load_dotenv
from pdf2image import convert_from_path, pdfinfo_from_path

from scripts.cbz_processor import compress_cbz
from scripts.utils import get_directory_from_env_or_prompt, make_summary_dict, print_result

TITLES = {
    "success": "Successfully converted",
    "warning": "Skipped file",
    "failed": "Failed to convert",
}


def clear_output_directory(output_directory, expected_directory_name):
    """Remove previously generated files from the output image directory."""
    if os.path.basename(output_directory) != expected_directory_name:
        raise ValueError(f"Refusing to clean unexpected directory: {output_directory}")

    generated_image_pattern = re.compile(
        rf"^{re.escape(expected_directory_name)}_\d{{3,}}\.png$"
    )

    try:
        for entry_name in os.listdir(output_directory):
            if not generated_image_pattern.fullmatch(entry_name):
                continue
            entry_path = os.path.join(output_directory, entry_name)
            os.remove(entry_path)
    except OSError as error:
        raise RuntimeError(f"Failed to clean output directory: {output_directory}") from error


def convert_pdf_to_image_directory(pdf_path):
    """Convert a PDF to sequentially named PNG files in a same-name directory."""
    directory = os.path.dirname(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_directory = os.path.join(directory, pdf_name)
    os.makedirs(output_directory, exist_ok=True)
    clear_output_directory(output_directory, pdf_name)

    page_count = int(pdfinfo_from_path(pdf_path)["Pages"])
    batch_size = 25
    for start_page in range(1, page_count + 1, batch_size):
        end_page = min(start_page + batch_size - 1, page_count)
        images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)
        for offset, image in enumerate(images):
            page_index = start_page + offset
            try:
                output_filename = f"{pdf_name}_{page_index:03}.png"
                output_path = os.path.join(output_directory, output_filename)
                image.save(output_path, "PNG")
            finally:
                image.close()

    return output_directory


def zip_directory(directory_path):
    """Create a zip archive from a directory and return the zip path."""
    zip_path = f"{directory_path}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(directory_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, directory_path)
                zip_file.write(file_path, arcname)
    return zip_path


def rename_zip_to_cbz(zip_path):
    """Rename a zip archive path to cbz and return the new path."""
    cbz_path = f"{os.path.splitext(zip_path)[0]}.cbz"
    os.replace(zip_path, cbz_path)
    return cbz_path


def convert_pdf_to_cbz(pdf_path, quality=80, max_height=1024):
    """Convert a PDF to CBZ and run CBZ optimization."""
    image_directory = convert_pdf_to_image_directory(pdf_path)
    zip_path = zip_directory(image_directory)
    cbz_path = rename_zip_to_cbz(zip_path)
    compress_cbz(cbz_path, quality=quality, max_height=max_height)
    return cbz_path


def process_pdf_files(directory, quality=80, max_height=1024):
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
                convert_pdf_to_cbz(file_path, quality=quality, max_height=max_height)
                print(f"✅ Converted: {file_path}")
                success_count += 1
            except Exception as error:
                print(f"🛑 Failed to convert {file_path}: {error}")
                failed_count += 1

    return make_summary_dict(success_count, skipped_count, failed_count)


def main():
    """Entry point for recursively converting PDFs to optimized CBZ files."""
    load_dotenv()
    directory = get_directory_from_env_or_prompt("PDF_TO_CBZ_DIR")
    print(f"Processing directory: {directory}")
    result = process_pdf_files(directory)
    print_result(result, TITLES)


if __name__ == "__main__":
    main()
