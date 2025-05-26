#!/usr/bin/env python3
"""
Enhanced Folder Scanner Script

This script scans a specified folder (and all its nested subfolders) for all files.
It outputs a directory tree structure and then detailed information for each file,
including filename, file type, location, and attempts to extract content and titles
for supported file types (currently .txt and .docx).

The output is saved to a text file named "folder_content_report.txt" in the
same directory as this script.

**REQUIREMENTS:**
This script requires the 'python-docx' library to process .docx files.
Install it using pip:
    pip install python-docx

Usage:
    python enhanced_folder_scanner.py [/path/to/folder]
    If no path is provided, the script will use the DEFAULT_FOLDER_PATH defined below.
"""

import os
import sys
import datetime
from pathlib import Path

try:
    from docx import Document
    # from docx.enum.style import WD_STYLE_TYPE # Not explicitly used, can be removed if not needed for future heading style checks
except ImportError:
    print("--------------------------------------------------------------------")
    print("WARNING: The 'python-docx' library is not installed or not found.")
    print("Microsoft Word (.docx) file content and title extraction will be SKIPPED.")
    print("To enable .docx processing, please install the library by running:")
    print("  pip install python-docx")
    print("--------------------------------------------------------------------")
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
                for line in lines: # Heuristic for title: first non-empty line
                    if line.strip():
                        title = line.strip()
                        if len(title) > 200: title = title[:200] + "..." # Cap title length
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
            titles_found = []
            # Try to find titles from heading styles
            for para in doc.paragraphs:
                # Check if style name exists and starts with 'Heading' (case-insensitive)
                if para.style and para.style.name and para.style.name.lower().startswith('heading'):
                    if para.text.strip(): # Ensure heading is not empty
                        titles_found.append(para.text.strip())
            
            if titles_found:
                title = "; ".join(titles_found[:3]) # Take first few headings as title
                if len(title) > 200: title = title[:200] + "..." # Cap title length
            elif doc.paragraphs: # Fallback to first non-empty paragraph if no headings
                 for para in doc.paragraphs:
                    if para.text.strip():
                        title_candidate = para.text.strip()
                        # Avoid overly long first paragraphs as titles
                        title = title_candidate[:150] + "..." if len(title_candidate) > 150 else title_candidate
                        break

            full_text_list = []
            for para in doc.paragraphs:
                full_text_list.append(para.text)
            full_text = "\n".join(full_text_list)

            if len(full_text) > MAX_CONTENT_PREVIEW_CHARS:
                content_preview = full_text[:MAX_CONTENT_PREVIEW_CHARS] + "\n... (content truncated)"
            elif len(full_text.splitlines()) > MAX_CONTENT_PREVIEW_LINES:
                content_preview = "\n".join(full_text.splitlines()[:MAX_CONTENT_PREVIEW_LINES]) + \
                                  "\n... (content truncated)"
            else:
                content_preview = full_text
            if not content_preview.strip() and not title: # If no text and no title derived
                content_notes = "[DOCX appears empty or has no extractable text/headings]"
            elif not content_preview.strip() and title:
                 content_notes = "[DOCX has headings but no other significant body text found for preview]"


        elif extension in ['.pdf', '.xlsx', '.xls', '.ppt', '.pptx']: # Placeholders for future extensions
            content_notes = f"[Content extraction for {extension} not yet implemented, but file is present.]"
            # Example for PDF (requires PyPDF2 or similar):
            # try:
            #   from PyPDF2 import PdfReader
            #   reader = PdfReader(filepath)
            #   if reader.metadata and reader.metadata.title:
            #       title = reader.metadata.title
            #   text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            #   content_preview = "\n".join(text_pages)[:MAX_CONTENT_PREVIEW_CHARS]
            #   if len(content_preview) == MAX_CONTENT_PREVIEW_CHARS: content_preview += "..."
            # except ImportError:
            #   content_notes = "[PyPDF2 library not installed. PDF processing skipped.]"
            # except Exception as e_pdf:
            #   content_notes = f"[Error processing PDF {path_obj.name}: {e_pdf}]"


        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', # Images
                           '.exe', '.dll', '.app', '.bin', # Executables / Binary
                           '.zip', '.gz', '.tar', '.rar', '.7z', # Archives
                           '.mp3', '.wav', '.aac', '.flac', # Audio
                           '.mp4', '.avi', '.mov', '.mkv', '.webm', # Video
                           '.lnk', '.url' # Shortcuts
                           ]:
            content_notes = f"[Binary, media, archive, or shortcut file ({extension}). Content not displayed.]"
            if extension == '.lnk':
                # Note: Robust .lnk parsing is complex and OS-dependent.
                # For Windows, 'pylnk3' library could be used.
                # For now, we just identify it.
                content_notes += " (Shortcut file)"
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
                    if content_preview.strip(): # Only add note if we actually got some text
                        content_notes = f"[Attempted text extraction for unknown type {extension}]"
                    else:
                        content_notes = f"[Unknown file type ({extension}), appears empty or unreadable as text]"
                else:
                    content_notes = f"[Unknown file type ({extension}), appears empty or unreadable as text]"
            except Exception:
                content_notes = f"[Unknown file type ({extension}), likely binary or not text-readable]"

    except Exception as e:
        content_notes = f"[ERROR processing file {path_obj.name}: {type(e).__name__} - {e}]"
        content_preview = "" # Ensure no partial content on error
        title = None # Ensure title is cleared on error

    return title, content_preview, content_notes


def generate_directory_tree(folder_path_str, output_file_object):
    """
    Generates a directory tree structure and writes it to the file.
    Uses pathlib for robust path handling.
    """
    base_folder_path = Path(folder_path_str)
    output_file_object.write(f"Directory Tree for: {base_folder_path}\n")
    output_file_object.write("="*50 + "\n")

    # Store paths to sort directories before files, and handle levels correctly
    paths_to_print = []

    for root, dirs, files in os.walk(base_folder_path):
        current_path = Path(root)
        relative_path = current_path.relative_to(base_folder_path)
        depth = len(relative_path.parts)

        # Add current directory to list
        paths_to_print.append({'name': current_path.name + ('/' if current_path != base_folder_path else '/'), 'depth': depth, 'is_dir': True, 'path_obj': current_path})
        
        # Sort dirs and files for consistent output
        dirs.sort()
        files.sort()

        for d_name in dirs:
            pass # Handled by the os.walk implicitly for structure, explicit printing done by depth
            
        for f_name in files:
            paths_to_print.append({'name': f_name, 'depth': depth + 1, 'is_dir': False, 'path_obj': current_path / f_name})

    # Simplified tree printing logic after collecting all paths
    # This part needs refinement for proper tree characters based on hierarchy
    # The initial example tree structure is complex to replicate perfectly without a dedicated library
    
    # Fallback to simple os.walk based printing (closer to original request)
    output_file_object.write(f"{base_folder_path.name}/\n")
    for root, dirs, files in os.walk(base_folder_path):
        current_path_obj = Path(root)
        level = len(current_path_obj.relative_to(base_folder_path).parts)
        
        dirs.sort() # Sort for consistent order
        files.sort()

        # Print directories at this level
        for d in dirs:
            indent = '│   ' * level + '├── '
            output_file_object.write(f"{indent}{d}/\n")

        # Print files at this level
        num_files = len(files)
        for i, f in enumerate(files):
            if i == num_files - 1 and not dirs: # Last item in this directory if no subdirs follow immediately
                 connector = '└── '
            else:
                 connector = '├── '
            indent = '│   ' * level + connector
            output_file_object.write(f"{indent}{f}\n")
            
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
        for file_name in files:
            all_files_paths.append(str(Path(root) / file_name)) # Use Path for robust join
    
    all_files_paths.sort() # Sort for consistent processing order
    return all_files_paths


def write_report_to_file(files_paths, output_file_path_obj, source_folder_str):
    """
    Write the collected file information, titles, and content to the output file.
    """
    with open(output_file_path_obj, 'w', encoding='utf-8') as f:
        f.write(f"FOLDER CONTENT REPORT\n")
        f.write(f"Source Folder: {source_folder_str}\n")
        f.write(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total files processed: {len(files_paths)}\n") # Changed from "found" to "processed"
        f.write("="*80 + "\n\n")

        # Generate and write the directory tree first
        print("Generating directory tree...")
        generate_directory_tree(source_folder_str, f) # Pass the source folder string
        
        f.write("DETAILED FILE INFORMATION:\n")
        f.write("="*80 + "\n\n")

        for i, file_path_str_item in enumerate(files_paths, 1):
            file_path_item = Path(file_path_str_item)
            print(f"Processing file {i}/{len(files_paths)}: {file_path_item.name}")

            f.write(f"--- File #{i} ---\n")
            f.write(f"Filename: {file_path_item.name}\n")
            
            file_extension = file_path_item.suffix if file_path_item.suffix else "[no extension]"
            f.write(f"Type: {file_extension.lower() if file_extension != '[no extension]' else file_extension}\n") # Ensure lowercase extension
            
            f.write(f"Location: {str(file_path_item)}\n")

            title, content_preview, content_notes = get_file_title_and_content(str(file_path_item))

            if title:
                f.write(f"Extracted Title(s)/Heading(s): {title}\n")
            
            if content_notes: # Always print notes if any
                f.write(f"Notes: {content_notes}\n")

            if content_preview and content_preview.strip(): # Check if preview has actual content
                f.write("Content Preview:\n\"\"\"\n")
                f.write(content_preview.strip())
                f.write("\n\"\"\"\n")
            # If no preview, but also no specific note saying why (e.g. binary file), it implies an issue or empty
            elif not content_notes or ("[Empty text file]" not in content_notes and "appears empty" not in content_notes and "Binary" not in content_notes and "not yet implemented" not in content_notes):
                 f.write("Content Preview: [Not available, file might be empty, or an issue occurred during extraction]\n")


            f.write("\n" + "-"*60 + "\n\n")
        
    print(f"\nScan complete! Results written to {output_file_path_obj}")
    print(f"Processed {len(files_paths)} files in total.")


def main():
    """Main function to execute the script."""
    if len(sys.argv) > 1:
        folder_path_arg = sys.argv[1]
    else:
        folder_path_arg = DEFAULT_FOLDER_PATH
        
        # More specific check for the placeholder path
        if DEFAULT_FOLDER_PATH == r"C:\Users\samue\Downloads\Sintica docs" or \
           DEFAULT_FOLDER_PATH.lower() == "/path/to/your/folder" or \
           not Path(DEFAULT_FOLDER_PATH).exists(): # Also check if default path doesn't exist
            print(f"INFO: Using default/placeholder FOLDER_PATH: {DEFAULT_FOLDER_PATH}")
            if not Path(DEFAULT_FOLDER_PATH).exists():
                print(f"WARNING: The default path '{DEFAULT_FOLDER_PATH}' does not exist.")
            print("Please change the DEFAULT_FOLDER_PATH variable in the script to your target folder,")
            print("or provide a valid path as a command-line argument.")
            print("Example: python your_script_name.py \"/actual/path/to/scan\"")
            if not Path(DEFAULT_FOLDER_PATH).exists(): # Exit if default path is bad and no arg given
                sys.exit("Script cannot proceed with a non-existent default path. Please provide a valid path.")

    # Normalize path and ensure it's absolute for clarity
    try:
        resolved_folder_path = str(Path(folder_path_arg).resolve(strict=True))
    except FileNotFoundError:
        print(f"ERROR: The specified folder path does not exist: {folder_path_arg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Invalid folder path specified: {folder_path_arg} ({e})")
        sys.exit(1)


    print(f"Starting scan for folder: {resolved_folder_path}")
    
    collected_files = scan_folder_and_collect_files(resolved_folder_path)
    
    # Output file is in the script's directory
    script_dir = Path(__file__).parent.resolve()
    output_path = script_dir / OUTPUT_FILE
    
    if not collected_files:
        print("No files found in the specified directory.")
        # Create an empty report or just a note
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"FOLDER CONTENT REPORT\n")
            f.write(f"Source Folder: {resolved_folder_path}\n")
            f.write(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("No files found in the specified directory.\n")
        print(f"Empty report written to {output_path}")
        return

    write_report_to_file(collected_files, output_path, resolved_folder_path)

if __name__ == "__main__":
    # The import try-except block for Document already prints a warning if python-docx is missing.
    main()