"""
CBZ Processor

This script compresses and optionally renames .cbz files in a specified directory.
It creates a backup of each original file before processing,
compresses images inside CBZ archives,
and can rename files according to user input.

Features:
    - Creates a backup of each original .cbz file as filename_original.cbz
    - Compresses images inside CBZ archives and optionally resizes them
    - Skips non-CBZ files
    - Reports the amount of space saved for each file
    - Prints a summary of processed, skipped, and failed files

Requirements:
    - Python 3.6+
    - Pillow (pip install pillow)

Usage:
    python cbz_processor.py
    # Then enter the directory and other options when prompted

Environment Variables:
    CBZ_PROCESSOR_DIR (optional): Directory path to process CBZ files in
"""

import os
import re
import shutil
import tempfile
import zipfile

from PIL import Image
from dotenv import load_dotenv

from scripts.utils import get_directory_from_env_or_prompt, print_result

TITLES = {
    "success": "Successfully optimized",
    "warning": "Skipped file",
    "failed": "Failed to process"
}

VALID_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

def get_file_size(file_path):
    """
    Returns the file size in megabytes.
    """
    size_in_bytes = os.path.getsize(file_path)
    return size_in_bytes / (1024 * 1024)

def _compress_and_write_image(img_path, temp_dir, zipf, quality, max_height):
    """
    Compress and optionally resize an image, then write it to the zip archive.
    """
    with Image.open(img_path) as img:
        if img.mode == 'P':
            img = img.convert('RGB')
        if img.height > max_height:
            aspect_ratio = img.width / img.height
            new_width = int(aspect_ratio * max_height)
            img = img.resize((new_width, max_height), Image.Resampling.LANCZOS)
        img_compressed_path = os.path.join(temp_dir, os.path.basename(img_path))
        img.save(img_compressed_path, "PNG", quality=quality)
        arcname = os.path.relpath(img_compressed_path, temp_dir)
        zipf.write(img_compressed_path, arcname)

def compress_cbz(file_path, output_path=None, quality=80, max_height=1024):
    """
    Compress images in a CBZ file and optionally resize them.
    Returns the size saved in MB.
    """
    if output_path is None:
        output_path = file_path
    original_size = get_file_size(file_path)
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        compressed_path = os.path.join(temp_dir, "compressed.cbz")
        with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(tuple(VALID_IMAGE_EXTENSIONS)):
                        img_path = os.path.join(root, file)
                        _compress_and_write_image(img_path, temp_dir, zipf, quality, max_height)
        size_saved = original_size - get_file_size(compressed_path)
        shutil.move(compressed_path, output_path)
    return size_saved

def clean_file_naming(filename, start_number):
    """
    Clean and rename the filename using the specified prefix and number.
    Currently not used in the main processing loop.
    """
    # Remove content inside parentheses
    cleaned_name = re.sub(r'\(.*?\)', '', filename)
    # Remove multiple consecutive spaces
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
    # Rename the file using the specified naming format
    _, extension = os.path.splitext(cleaned_name)
    cleaned_name = f"{cleaned_name} {start_number:03}{extension}"
    return cleaned_name

def process_cbz_files(directory, quality, max_height):
    """
    Compress .cbz files in the given directory.
    For each file:
        - Create a backup as filename_original.cbz
        - Compress images inside the CBZ
        - Print the amount of space saved
    Returns a summary dict for print_result.
    """
    counts = {
        "success_count": 0,
        "skipped_count": 0,
        "failed_count": 0
    }

    def backup_and_compress_cbz(filepath, filename):
        base, ext = os.path.splitext(filename)
        original_copy_path = os.path.join(directory, f"{base}_original{ext}")
        print(f"Creating backup: {original_copy_path}")
        shutil.copy2(filepath, original_copy_path)
        size_saved = compress_cbz(filepath, quality=quality, max_height=max_height)
        print(f"✅ Optimized {os.path.basename(filepath)} | Size saved: {size_saved:.2f} MB")
        return size_saved

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if filename.endswith('.cbz'):
            try:
                backup_and_compress_cbz(filepath, filename)
                counts["success_count"] += 1
            except Exception as e:
                print(f"🛑 Failed to process {filename}: {e}")
                counts["failed_count"] += 1
        else:
            counts["skipped_count"] += 1
    return counts

def main():
    """
    Main entry point for the CBZ processor script.
    Handles user interaction, compression, backup creation, and summary output.
    """
    load_dotenv()
    directory = get_directory_from_env_or_prompt('CBZ_PROCESSOR_DIR')
    quality = 80
    max_height = 1024
    print(f"📁 Processing directory: {directory}")
    result = process_cbz_files(directory, quality, max_height)
    print_result(result, TITLES)

if __name__ == "__main__":
    main()
