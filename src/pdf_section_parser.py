# src/pdf_section_parser.py

import fitz
import re


# Heading patterns supported:
#   Numbered  : "1.", "4.2", "3.1.2 Title"
#   Lettered  : "A.", "B. Overview"
#   ALL CAPS  : "OVERVIEW", "TECHNICAL REQUIREMENTS" (min 4 chars, no digits)

NUMBERED_HEADING = re.compile(r"^\d+(\.\d+)*\s+\S+")
LETTERED_HEADING = re.compile(r"^[A-Z]\.\s+\S+")
ALL_CAPS_HEADING = re.compile(r"^[A-Z][A-Z\s]{3,}$")


def _is_heading(line):
    """
    Returns True if the line matches any known heading pattern.
    Expand patterns here as needed for new RFP formats.
    """
    if NUMBERED_HEADING.match(line):
        return True

    if LETTERED_HEADING.match(line):
        return True

    # ALL CAPS check: skip lines that are just a single word of 3 chars or less
    if ALL_CAPS_HEADING.match(line) and len(line.split()) > 1:
        return True

    return False


def parse_pdf_sections(pdf_path, start_page, end_page):
    """
    Parses a PDF and returns structured sections as a list of tuples:
        [(heading, [bullet_line, bullet_line, ...]), ...]

    Supported heading formats:
    - Numbered  : "1.", "4.2", "3.1.2 Title"
    - Lettered  : "A. Overview"
    - ALL CAPS  : "TECHNICAL REQUIREMENTS"

    Note: Detection relies on text patterns, not font/style metadata.
    PDFs with non-standard formatting may require additional pattern rules.

    Args:
        pdf_path   : Path to the PDF file.
        start_page : 1-based start page index.
        end_page   : 1-based end page index (inclusive).

    Returns:
        List of (heading_str, [content_lines]) tuples.
    """

    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Clamp to actual document length
    end_page = min(end_page, total_pages)

    sections = []
    current_heading = None
    current_bullets = []

    print(f"\nParsing pages {start_page} to {end_page} of {total_pages} total\n")

    for page_num in range(start_page - 1, end_page):

        page = doc[page_num]
        text = page.get_text()
        lines = text.split("\n")

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if _is_heading(line):
                # Save completed section before starting new one
                if current_heading:
                    sections.append((current_heading, current_bullets))

                current_heading = line
                current_bullets = []

            else:
                # Non-heading lines treated as content/bullets
                if current_heading:
                    current_bullets.append(line)

    # Append final section
    if current_heading:
        sections.append((current_heading, current_bullets))

    print(f"Total sections detected: {len(sections)}\n")

    return sections