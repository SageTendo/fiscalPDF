from pathlib import Path
import fitz
import pymupdf
from pymupdf import Document, FileDataError
import re
import numpy as np

from error import (
    FailedToExtractCreditNotesException,
    PathNotFoundException,
    PathNotPDFFileException,
    NothingToModifyException,
)
from config import OUTPUT_DIR


CREDIT_NOTE_PATTERN = r"Credit Note:\s*[\w/]+"


def open_pdf_document(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise PathNotFoundException(file_path)

    if not Path.is_file(path) or path.suffix.lower() != ".pdf":
        raise PathNotPDFFileException(file_path)

    try:
        return pymupdf.open(file_path)
    except FileDataError as e:
        raise PathNotPDFFileException(file_path) from e


def get_pages_with_credit_notes(document: Document):
    pages = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        if re.search(CREDIT_NOTE_PATTERN, page.get_text()):  # type: ignore
            pages.append(page_num)
    return pages


def extract_credit_notes(extracted: str):
    return re.findall(CREDIT_NOTE_PATTERN, extracted, re.IGNORECASE)


def get_output_path(filename: str):
    output_name = f"modified_{Path(filename).name}"
    return OUTPUT_DIR.joinpath(output_name)


def replace_matches_in_pdf(document: fitz.Document, pages, replace_text: str):
    """
    Rebuilds each page with replaced text inline, preserving layout order and font sizes.
    """
    if not pages:
        raise NothingToModifyException(document.name)  # type: ignore

    new_doc = fitz.open()
    for page_num in pages:
        page = document.load_page(page_num)
        text_dict = page.get_text("dict")  # pyright: ignore[reportAttributeAccessIssue]
        page_rect = page.rect

        new_page = new_doc.new_page(  # type: ignore
            width=page_rect.width, height=page_rect.height
        )

        # Iterate through all graphics and redraw them
        paths = page.get_drawings()
        shape = new_page.new_shape()
        for path in paths:
            # ------------------------------------
            # draw each entry of the 'items' list
            # ------------------------------------
            for item in path["items"]:
                if item[0] == "l":  # line
                    shape.draw_line(item[1], item[2])
                elif item[0] == "re":  # rectangle
                    shape.draw_rect(item[1])
                elif item[0] == "qu":  # quad
                    shape.draw_quad(item[1])
                elif item[0] == "c":  # curve
                    shape.draw_bezier(item[1], item[2], item[3], item[4])
                else:
                    raise ValueError("unhandled drawing", item)
            # ------------------------------------------------------
            # all items are drawn, now apply the common properties
            # to finish the path
            # ------------------------------------------------------
            # Safely extract and normalize values
            line_join = path.get("lineJoin")
            if line_join is None:
                line_join = 0

            line_cap = path.get("lineCap")
            if isinstance(line_cap, (list, tuple)):
                line_cap = max(line_cap)
            elif line_cap is None:
                line_cap = 0

            stroke_opacity = path.get("stroke_opacity") or 1.0
            fill_opacity = path.get("fill_opacity") or 1.0

            color = path.get("color")
            fill = path.get("fill")
            dashes = path.get("dashes")

            width = path.get("width")
            if width is None:
                width = 1.0

            # Apply the finished style safely
            shape.finish(
                fill=fill,
                color=color,
                dashes=dashes,
                even_odd=path.get("even_odd", True),
                closePath=path.get("closePath", False),
                lineJoin=line_join,
                lineCap=line_cap,
                width=width,
                stroke_opacity=stroke_opacity,
                fill_opacity=fill_opacity,
            )

        # all paths processed - commit the shape to its page
        shape.commit()

        # iterate over all images on the page
        image_infos = page.get_image_info(xrefs=True)
        for info in image_infos:
            xref = info["xref"]
            bbox = info["bbox"]

            if bbox is None:
                # fallback — if bbox not found, draw full page
                bbox = page.rect

            # make a pixmap for the image
            pix = pymupdf.Pixmap(document, xref)

            # draw the image at the same position
            new_page.insert_image(bbox, pixmap=pix)
            pix = None  # free memory

        # Iterate through all spans and rebuild text
        for block in text_dict["blocks"]:  # type: ignore
            for line in block.get("lines", []):  # type: ignore
                for span in line.get("spans", []):
                    text = span["text"]
                    if re.search(CREDIT_NOTE_PATTERN, text, re.IGNORECASE):
                        text = re.sub(
                            CREDIT_NOTE_PATTERN, replace_text, text, flags=re.IGNORECASE
                        )

                    # Draw text at the same location
                    new_page.insert_text(
                        (span["bbox"][0], span["bbox"][1] + 6),
                        text,
                        fontsize=span["size"],
                        fontname="helv",  # use standard font to avoid missing font errors
                        color=(0, 0, 0),
                    )

    output_path = get_output_path(document.name)  # pyright: ignore[reportArgumentType]
    new_doc.save(output_path, deflate=True)
    new_doc.close()


def redact_matches_in_pdf_with(document: Document, pages, replace_text: str):
    if not pages:
        raise NothingToModifyException(document.name)  # type: ignore

    output_path = get_output_path(document.name)  # type: ignore
    for page_num in pages:
        page = document.load_page(page_num)
        text_insertion_positions = []

        extracted_credit_notes = extract_credit_notes(page.get_text())  # type: ignore
        if not extracted_credit_notes:
            raise FailedToExtractCreditNotesException(document.name)  # type: ignore

        # Redact and find positions to place replacement text
        for credit_note in extracted_credit_notes:
            areas = page.search_for(credit_note, flags=0)  # type: ignore
            for area in areas:
                center = area.tl + (area.br - area.tl) * 0.5
                smaller_area = fitz.Rect(
                    center.x + (area.x0 - center.x),
                    center.y + (area.y0 - center.y) * 0.2,
                    center.x + (area.x1 - center.x) * 1.2,
                    center.y + (area.y1 - center.y) * 0.5,
                )

                text_position = np.array([smaller_area[0], smaller_area[1]]) + np.array(
                    [0, (smaller_area[3] - smaller_area[1]) + 1]
                )
                text_insertion_positions.append(text_position)
                page.add_redact_annot(smaller_area, fill=(1, 1, 1))
        page.apply_redactions()  # type: ignore

        # Place text on top of redactions
        for text_position in text_insertion_positions:
            text_position = tuple(text_position)
            page.insert_text(text_position, replace_text, fontsize=6.5)  # type: ignore
    document.save(output_path, deflate=True)


if __name__ == "__main__":
    pdf = open_pdf_document("in/19912-October 25.pdf")
    pages_with_credit_notes = get_pages_with_credit_notes(pdf)
    replace_matches_in_pdf(pdf, pages_with_credit_notes, "CN")
