from pathlib import Path
import fitz
import pymupdf
from pymupdf import Document
import re
import numpy as np

from error import (
    NothingToModifyException,
    PathNotFoundException,
    PathNotPDFFileException,
)


class PAD:
    """
    Helper class for text box redaction padding
    T: Top
    B: Bottom
    L: Left
    R: Right
    """

    T = 6
    B = -1
    L = -4
    R = 4


CREDIT_NOTE_PATTERN = r"Credit Note:\s*[\w/]+"
FLAGS = [re.IGNORECASE, re.MULTILINE, re.DOTALL]
SHRINK_WIDTH_BY = 0


# TODO: Remove default later
def open_pdf_document(file_path: Path = Path("19972-0ct 25.pdf")):
    path = Path(file_path)
    if not path.exists():
        raise PathNotFoundException(file_path)

    if not Path.is_file(path):
        raise PathNotPDFFileException(file_path)
    return pymupdf.open(file_path)


def get_pages_with_credit_notes(document: Document):
    pages_with_credit_notes = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        if re.search(CREDIT_NOTE_PATTERN, page.get_text()):
            pages_with_credit_notes.append(page_num)
    return pages_with_credit_notes


def extract_credit_notes(extracted: str):
    return re.findall(CREDIT_NOTE_PATTERN, extracted, re.IGNORECASE)


def replace_matches_in_pdf(
    document: Document, pages, replace_text: str, output_path: Path
):
    # Iterate through each page in the PDF
    for page_num in pages:
        page = document.load_page(page_num)
        text_insertion_positions = []

        extracted_credit_notes = extract_credit_notes(page.get_text())
        if not extracted_credit_notes:
            raise NothingToModifyException(document.name)

        # Redact and find positions to place replacement text
        for credit_note in extracted_credit_notes:
            areas = page.search_for(credit_note, flags=0)            
            for area in areas:
                center = area.tl + (area.br - area.tl) * 0.5
                smaller_area = fitz.Rect(
                    center.x + (area.x0 - center.x),
                    center.y + (area.y0 - center.y) * 0.2,
                    center.x + (area.x1 - center.x) * 1.2,
                    center.y + (area.y1 - center.y) * 1,
                )

                text_position = np.array([smaller_area[0], smaller_area[1]]) + np.array(
                    [0, (smaller_area[3] - smaller_area[1]) / 2]
                )
                text_insertion_positions.append(text_position)
                page.add_redact_annot(smaller_area, fill=(1, 1, 1))
        page.apply_redactions()

        # Place text on top of redactions
        for text_position in text_insertion_positions:
            text_position = tuple(text_position)
            page.insert_text(text_position, replace_text, fontsize=6)
    document.save(output_path)


def main():
    document = open_pdf_document("19912-October 25.pdf")
    pages_with_credit_notes = get_pages_with_credit_notes(document)
    replace_matches_in_pdf(document, pages_with_credit_notes, "CN", Path("./out.pdf"))


main()
