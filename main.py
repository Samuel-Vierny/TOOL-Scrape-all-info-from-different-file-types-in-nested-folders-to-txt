#!/usr/bin/env python3
"""
Enhanced Folder Scanner Script

This script scans a specified folder (and all its nested subfolders) for all files.
It outputs a directory tree structure and then detailed information for each file,
including filename, file type, location, and attempts to extract content and titles
for supported file types (currently .txt and .docx).

The output is saved to a text file named "folder_content_report.txt" in the
same directory as this script.

Usage:
    python enhanced_folder_scanner.py [/path/to/folder]
    If no path is provided, the script will use the FOLDER_PATH defined below.

Requires:
    pip install python-docx
"""

import os
import sys
import datetime
from pathlib import Path

try:
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
except ImportError:
    print("Requirement 'python-docx' not found. Please install it: pip install python-docx")
    print("DOCX file processing will be skipped.")
    Document = None # Placeholder if import fails

#-------------------------------------------------------------------------
# CONFIGURATION - CHANGE THIS SECTION AS NEEDED
#-------------------------------------------------------------------------
# Set the path to the folder you want to scan here
# IMPORTANT: Use forward slashes (/) or double backslashes (\\) for Windows paths
DEFAULT_FOLDER_PATH = r"C:\Users\samue\Downloads\Sintica docs"  # <- CHANGE THIS PATH if not using CLI arg

# Name of the output file (will be created in the same directory as this script)
OUTPUT_FILE = "folder_content_report.txt"

# Content preview settings
MAX_CONTENT_PREVIEW_LINES = 50
MAX_CONTENT_PREVIEW_CHARS = 2000
#-------------------------------------------------------------------------

def get_file_title_and_content(filepath):
    """
    Attempts to extract a title and content from a given file.
    """
    path_obj = Path(filepath)
    extension = path_obj.suffix.lower()
    title = None
    content_preview = ""
    content_notes = ""

    try:
        if extension == ".txt":
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            if lines:
                # Heuristic for title: first non-empty line
                for line in lines:
                    if line.strip():
                        title = line.strip()
                        break
                full_content = "".join(lines)
                if len(full_content) > MAX_CONTENT_PREVIEW_CHARS:
                    content_preview = full_content[:MAX_CONTENT_PREVIEW_CHARS] + "\n... (content truncated)"
                elif len(lines) > MAX_CONTENT_PREVIEW_LINES:
                    content_preview = "".join(lines[:MAX_CONTENT_PREVIEW_LINES]) + "\n... (content truncated)"
                else:
                    content_preview = full_content
            else:
                content_notes = "[Empty text file]"

        elif extension == ".docx" and Document is not None:
            doc = Document(filepath)
            titles = []
            # Try to find titles from heading styles
            for para in doc.paragraphs:
                if para.style and para.style.name.startswith('Heading'):
                    titles.append(para.text.strip())
            if titles:
                title = "; ".join(titles[:3]) # Take first few headings as title
            elif doc.paragraphs: # Fallback to first non-empty paragraph if no headings
                 for para in doc.paragraphs:
                    if para.text.strip():
                        title = para.text.strip()
                        if len(title) > 150: title = title[:150] + "..."
                        break

            full_text = "\n".join([para.text for para in doc.paragraphs])
            if len(full_text) > MAX_CONTENT_PREVIEW_CHARS:
                content_preview = full_text[:MAX_CONTENT_PREVIEW_CHARS] + "\n... (content truncated)"
            elif len(full_text.splitlines()) > MAX_CONTENT_PREVIEW_LINES:
                content_preview = "\n".join(full_text.splitlines()[:MAX_CONTENT_PREVIEW_LINES]) + \
                                  "\n... (content truncated)"
            else:
                content_preview = full_text
            if not content_preview.strip():
                content_notes = "[DOCX has no extractable text or is empty]"

        elif extension in ['.pdf', '.xlsx', '.xls']: # Placeholders for future extensions
            content_notes = f"[Content extraction for {extension} not yet implemented, but file is present.]"
            # Example for PDF (requires PyPDF2 or similar):
            # from PyPDF2 import PdfReader
            # reader = PdfReader(filepath)
            # title = reader.metadata.title if reader.metadata else None
            # text_pages = [page.extract_text() for page in reader.pages]
            # content_preview = "\n".join(text_pages)[:MAX_CONTENT_PREVIEW_CHARS] + "..."

        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.exe', '.dll', '.zip', '.gz', '.tar', '.rar', '.mp3', '.mp4', '.avi', '.mov', '.lnk']:
            content_notes = f"[Binary or non-text file ({extension}). Content not displayed.]"
            if extension == '.lnk':
                try:
                    # This is a very basic way to read .lnk on Windows.
                    # For a robust solution, a library like 'pylnk' might be needed.
                    # This often doesn't work directly for all .lnk files without specific parsing.
                    # For now, we'll just mark it.
                    # import struct
                    # with open(filepath, 'rb') as f:
                    #    content = f.read()
                    #    # Extremely simplified and likely non-functional lnk parsing attempt
                    #    if content[0:4] == b'\x4C\x00\x00\x00' and content[0x14:0x18] == b'\x01\x14\x02\x00':
                    #       # This is not a reliable way to get the target
                    #       content_notes += " (Shortcut - target extraction needs a dedicated library)"
                    pass

                except Exception as e:
                    content_notes += f" (Error trying to inspect lnk: {e})"


        else:
            # Try to read as text for unknown types, but be cautious
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                if lines:
                    full_content = "".join(lines)
                    if len(full_content) > MAX_CONTENT_PREVIEW_CHARS:
                        content_preview = full_content[:MAX_CONTENT_PREVIEW_CHARS] + "\n... (content truncated)"
                    elif len(lines) > MAX_CONTENT_PREVIEW_LINES:
                        content_preview = "".join(lines[:MAX_CONTENT_PREVIEW_LINES]) + "\n... (content truncated)"
                    else:
                        content_preview = full_content
                    content_notes = f"[Attempted text extraction for unknown type {extension}]"
                else:
                    content_notes = f"[Unknown file type ({extension}), appears empty or unreadable as text]"
            except Exception:
                content_notes = f"[Unknown file type ({extension}), likely binary or not text-readable]"

    except Exception as e:
        content_notes = f"[Error processing file {path_obj.name}: {e}]"
        content_preview = "" # Ensure no partial content on error

    return title, content_preview, content_notes


def generate_directory_tree(folder_path, output_file_object):
    """
    Generates a directory tree structure and writes it to the file.
    """
    output_file_object.write(f"Directory Tree for: {folder_path}\n")
    output_file_object.write("="*50 + "\n")
    root_path = Path(folder_path)
    
    for root, dirs, files in os.walk(folder_path):
        level = Path(root).relative_to(root_path).parts
        indent = '│   ' * (len(level) -1) + '├── ' if level else ''
        
        # Ensure the root folder itself is printed if it's the starting point
        if not level:
             output_file_object.write(f"{root_path.name}/\n")
        else:
            output_file_object.write(f"{'│   ' * (len(level)-1)}├── {Path(root).name}/\n")

        sub_indent = '│   ' * len(level) + '│   '
        file_prefix = '│   ' * len(level) + '└── ' if not dirs else '│   ' * len(level) + '├── '
        
        # Sort directories and files for consistent output
        dirs.sort()
        files.sort()

        # Print files in the current directory
        for i, f_name in enumerate(files):
            is_last_file = (i == len(files) - 1)
            prefix = '│   ' * len(level) + ('└── ' if is_last_file and not any(d for d in dirs if d > f_name) else '├── ') # complex logic for tree
            output_file_object.write(f"{prefix}{f_name}\n")
            
    output_file_object.write("="*50 + "\n\n")


def scan_folder_and_collect_files(folder_path):
    """
    Recursively scan a folder and collect all file paths.
    """
    all_files_paths = []
    root_path_obj = Path(folder_path)

    if not root_path_obj.exists():
        print(f"Error: The path '{folder_path}' does not exist.")
        sys.exit(1)
    if not root_path_obj.is_dir():
        print(f"Error: '{folder_path}' is not a directory.")
        sys.exit(1)

    for root, _, files in os.walk(folder_path):
        for file in files:
            all_files_paths.append(os.path.join(root, file))
    
    all_files_paths.sort() # Sort for consistent processing order
    return all_files_paths


def write_report_to_file(files_paths, output_file_path, source_folder):
    """
    Write the collected file information, titles, and content to the output file.
    """
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(f"FOLDER CONTENT REPORT\n")
        f.write(f"Source Folder: {source_folder}\n")
        f.write(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total files found: {len(files_paths)}\n")
        f.write("="*80 + "\n\n")

        # Generate and write the directory tree first
        print("Generating directory tree...")
        generate_directory_tree(source_folder, f)
        
        f.write("DETAILED FILE INFORMATION:\n")
        f.write("="*80 + "\n\n")

        for i, file_path_str in enumerate(files_paths, 1):
            file_path = Path(file_path_str)
            print(f"Processing file {i}/{len(files_paths)}: {file_path.name}")

            f.write(f"--- File #{i} ---\n")
            f.write(f"Filename: {file_path.name}\n")
            
            file_extension = file_path.suffix if file_path.suffix else "[no extension]"
            f.write(f"Type: {file_extension}\n")
            
            f.write(f"Location: {str(file_path)}\n")

            title, content_preview, content_notes = get_file_title_and_content(str(file_path))

            if title:
                f.write(f"Extracted Title(s)/Heading(s): {title}\n")
            
            if content_notes:
                f.write(f"Notes: {content_notes}\n")

            if content_preview.strip():
                f.write("Content Preview:\n\"\"\"\n")
                f.write(content_preview.strip())
                f.write("\n\"\"\"\n")
            elif not content_notes: # If no preview and no specific note, mention it
                 f.write("Content Preview: [Not available or file is empty]\n")

            f.write("\n" + "-"*60 + "\n\n")
        
    print(f"\nScan complete! Results written to {output_file_path}")
    print(f"Processed {len(files_paths)} files in total.")


def main():
    """Main function to execute the script."""
    if len(sys.argv) > 1:
        folder_path_arg = sys.argv[1]
    else:
        folder_path_arg = DEFAULT_FOLDER_PATH
        
        if DEFAULT_FOLDER_PATH == r"C:\Users\samue\Downloads\Sintica docs" or DEFAULT_FOLDER_PATH == "/path/to/your/folder": # Check generic default
            print(f"INFO: Using default FOLDER_PATH: {DEFAULT_FOLDER_PATH}")
            print("You can change this in the script or provide a path as a command-line argument.")
            # Optional: ask for confirmation if using a very default path
            # response = input(f"Continue with '{DEFAULT_FOLDER_PATH}'? (y/n): ")
            # if response.lower() != 'y':
            #     sys.exit("Scan aborted by user.")

    # Normalize path
    folder_path = str(Path(folder_path_arg).resolve()) # Get absolute path

    print(f"Starting scan for folder: {folder_path}")
    
    collected_files = scan_folder_and_collect_files(folder_path)
    
    script_dir = Path(__file__).parent.resolve()
    output_path = script_dir / OUTPUT_FILE
    
    if not collected_files:
        print("No files found in the specified directory.")
        # Create an empty report or just a note
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"FOLDER CONTENT REPORT\n")
            f.write(f"Source Folder: {folder_path}\n")
            f.write(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("No files found in the specified directory.\n")
        print(f"Empty report written to {output_path}")
        return

    write_report_to_file(collected_files, output_path, folder_path)

if __name__ == "__main__":
    if Document is None and '--skip-docx-check' not in sys.argv:
        print("\nNote: 'python-docx' library is not installed or failed to import.")
        print("DOCX file content and title extraction will be skipped.")
        print("Install it with 'pip install python-docx' for full functionality.")
        # proceed = input("Continue without DOCX processing? (y/n): ")
        # if proceed.lower() != 'y':
        #     sys.exit("Aborted by user.")
    main()