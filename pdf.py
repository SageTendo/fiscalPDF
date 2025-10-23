from datetime import datetime
from pathlib import Path
import fitz
import pymupdf
from pymupdf import Document, FileDataError
import re

from error import (
    PDFCreationFailException,
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


def get_output_path(filename: str, output_dir=OUTPUT_DIR):
    output_name = f"modified_{Path(filename).name}"
    return output_dir.joinpath(output_name)


def _draw_graphics_onto_canvas(paths, canvas):
    """
    Reconstructs and draws vector graphics paths onto a given PDF canvas.

    This function iterates through a list of path definitions extracted from a PDF,
    replays each drawing operation (lines, rectangles, quads, and curves), and then
    applies shared graphical properties such as stroke, fill, opacity, and line styles.
    Once all paths are drawn, the canvas is finalized with `canvas.commit()`.

    Args:
        paths (list[dict]): A list of path definitions, where each dictionary may contain:
            - "items" (list[tuple]): Drawing operations and their parameters.
              Example item formats:
                - ("l", point1, point2): Draws a line from `point1` to `point2`.
                - ("re", rect): Draws a rectangle with the given bounding box.
                - ("qu", quad): Draws a quadrilateral (four-point polygon).
                - ("c", p1, p2, p3, p4): Draws a cubic Bézier curve.
            - "lineJoin" (int, optional): Specifies how lines are joined (default: 0).
            - "lineCap" (int | list[int], optional): Specifies how line endings are drawn.
              If a list or tuple is given, the maximum value is used.
            - "stroke_opacity" (float, optional): Opacity for strokes (default: 1.0).
            - "fill_opacity" (float, optional): Opacity for fills (default: 1.0).
            - "color" (tuple[float, float, float], optional): Stroke color (RGB values in [0,1]).
            - "fill" (tuple[float, float, float], optional): Fill color (RGB values in [0,1]).
            - "dashes" (list[float], optional): Dash pattern for strokes.
            - "width" (float, optional): Line width (default: 1.0).
            - "even_odd" (bool, optional): Whether to use even-odd rule for filling (default: True).
            - "closePath" (bool, optional): Whether to close the path (default: False).

        canvas (fitz.Canvas): A PyMuPDF canvas object used to render the reconstructed vector graphics.

    Raises:
        PDFCreationFailException: If an unrecognized drawing operation is encountered
        or an invalid path structure is detected.

    Notes:
        - Each path is processed independently and then finalized with its shared graphical
          properties via `canvas.finish(...)`.
        - After all paths are drawn, `canvas.commit()` must be called to apply the changes
          to the page.
        - Default fallback values are provided for missing attributes (e.g., width, join style).

    Example:
        >>> paths = [
        ...     {
        ...         "items": [("l", (10, 10), (100, 100))],
        ...         "color": (0, 0, 0),
        ...         "width": 2.0,
        ...     }
        ... ]
        >>> _draw_graphics_onto_canvas(paths, canvas)
    """
    for path in paths:
        for item in path["items"]:
            if item[0] == "l":  # line
                canvas.draw_line(item[1], item[2])
            elif item[0] == "re":  # rectangle
                canvas.draw_rect(item[1])
            elif item[0] == "qu":  # quad
                canvas.draw_quad(item[1])
            elif item[0] == "c":  # curve
                canvas.draw_bezier(item[1], item[2], item[3], item[4])
            else:
                raise PDFCreationFailException(f"Unhandled drawing: {item}")

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

        canvas.finish(
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
    canvas.commit()


def _draw_images_onto_page(document, original_page, new_page, image_info_list):
    """
    Draws images from an existing PDF page onto a new page, preserving their original positions.

    This function iterates through a list of image metadata entries (xref and bounding box),
    retrieves each image as a pixmap, and inserts it into the new page at the corresponding
    bounding box coordinates. If an image has no bounding box, the full page area is used
    as a fallback. If an image reference (xref) is invalid (0), a default value of 11 is used
    based on empirical observations from previously processed PDFs.

    Args:
        document (fitz.Document): The PDF document object containing image references.
        original_page (fitz.Page): The source page from which image bounding boxes are derived.
        new_page (fitz.Page): The destination page to which images will be drawn.
        image_info_list (list[dict]): A list of dictionaries containing image metadata.
            Each dictionary should include:
                - "xref" (int): The image reference ID in the PDF.
                - "bbox" (fitz.Rect | None): The bounding box defining where the image appears.

    Raises:
        PDFCreationFailException: If an image cannot be rendered or inserted due to
            invalid references or pixmap errors.

    Notes:
        - If `bbox` is missing or `None`, the image is drawn over the full page.
        - If `xref` equals 0, it defaults to 11 (a workaround for certain malformed PDFs
          where image references were missing but 11 was valid).
        - The image is inserted using `page.insert_image(bbox, pixmap=pix)` to preserve
          aspect ratio and positioning.
    """
    for info in image_info_list:
        xref = info["xref"]
        bbox = info["bbox"]

        if bbox is None:  # fallback — if bbox not found, draw full page
            bbox = original_page.rect

        if xref == 0:
            xref = 11

        try:
            pix = pymupdf.Pixmap(document, xref)
            new_page.insert_image(bbox, pixmap=pix)
        except ValueError as err:
            raise PDFCreationFailException(f"Failed to render graphics to page: {err}")


def _draw_text_onto_page(page: fitz.Page, text_blocks: list[dict], replace_text: str):
    """
    Redraws text onto a PDF page, replacing matches of a given pattern with new text,
    while preserving the original positioning of each text span.

    This function iterates through all text blocks and their corresponding lines and spans,
    extracts the bounding box coordinates, and re-inserts the text onto the page. The
    bottom-left point of the bounding box (x1, y2) is used as the insertion point to ensure
    alignment with the original layout.

    As Illustrated:
        (x1, y1) -> ---------- <- (x2, y1)
                    |          |
        (x1, y2) -> ---------- <- (x2, y2)

    Args:
        page (fitz.Page): The PDF page object to draw text onto.
        text_blocks (list[dict]): A list of text block dictionaries obtained from
            `page.get_text("dict")`. Each block contains lines, and each line contains spans
            with text and bounding box coordinates.
        replace_text (str): The replacement text that substitutes any substring matching
            `CREDIT_NOTE_PATTERN`.

    Raises:
        PDFCreationFailException: If a span is missing a bounding box or text, or if text
        insertion fails for any reason.

    Notes:
        - The indices `0` and `3` from the bounding box represent `x1` (leftmost x-coordinate)
        and `y2` (bottom y-coordinate), ensuring proper alignment with the original text baseline.
        - The inserted text uses the "helv" font (a standard Helvetica font) to prevent
    """
    bbox_x = 0
    bbox_y = 3

    for block in text_blocks:  # type: ignore
        for line in block.get("lines", []):  # type: ignore
            for span in line.get("spans", []):
                bbox = span.get("bbox")
                if not bbox:
                    raise PDFCreationFailException(
                        "Failed to redraw text to page: No bounding box found"
                    )

                text = span.get("text")
                if not text:
                    raise PDFCreationFailException(
                        "Failed to redraw text to page: No text found"
                    )

                if re.search(CREDIT_NOTE_PATTERN, text, re.IGNORECASE):
                    text = re.sub(
                        CREDIT_NOTE_PATTERN, replace_text, text, flags=re.IGNORECASE
                    )
                page.insert_text(
                    (bbox[bbox_x], bbox[bbox_y]),
                    text,
                    fontsize=span["size"],
                    fontname="helv",  # use standard font to avoid missing font errors
                    color=(0, 0, 0),
                )


def replace_matches_in_pdf(
    document: fitz.Document, pages, replace_text: str
) -> Document:
    """
    Creates a new PDF document where matched text patterns are replaced with the given text,
    while preserving the original graphics, images, and layout of each page.

    This function reconstructs each specified page by:
    1. Copying its vector graphics (shapes, lines, rectangles, curves).
    2. Redrawing embedded images in their original positions.
    3. Rewriting text content, performing regex-based replacements where applicable.

    Args:
        document (fitz.Document): The source PDF document to process.
        pages (list[int]): A list of page indices (0-based) to process.
        replace_text (str): The text that replaces any matches found by
            the defined regex pattern (typically `CREDIT_NOTE_PATTERN`).

    Returns:
        fitz.Document: A new PDF document with the replaced text and preserved visual layout.

    Raises:
        NothingToModifyException: If no pages are provided for modification.
        PDFCreationFailException: If any step in extracting or reconstructing page
            contents fails (e.g., missing text blocks, invalid drawing data).

    Notes:
        - This function does not modify the original document; it creates a new one.
        - Text replacement uses case-insensitive regex matching.
        - Vector paths and images are redrawn before text to preserve layering order.
        - The layout (page size, positions, colors) is maintained as closely as possible.

    Example:
        >>> import fitz
        >>> doc = fitz.open("invoice.pdf")
        >>> pages_to_modify = [0, 2]
        >>> updated_doc = replace_matches_in_pdf(doc, pages_to_modify, "Tax Invoice")
        >>> updated_doc.save("updated_invoice.pdf")
    """
    if not pages:
        raise NothingToModifyException(document.name)  # type: ignore

    new_document = fitz.open()
    for page_num in pages:
        original_page = document.load_page(page_num)
        page_rect = original_page.rect
        new_page = new_document.new_page(  # type: ignore
            width=page_rect.width, height=page_rect.height
        )

        paths = original_page.get_drawings()
        shape = new_page.new_shape()
        image_info_list = original_page.get_image_info(xrefs=True)
        text_dict = original_page.get_text(
            "dict"
        )  # pyright: ignore[reportAttributeAccessIssue]

        if not isinstance(text_dict, dict):
            raise PDFCreationFailException(
                "Could not extract page contents as a text dictionary"
            )
        if "blocks" not in text_dict:
            raise PDFCreationFailException(
                "Could not extract content blocks from text dictionory"
            )

        _draw_graphics_onto_canvas(paths, shape)
        _draw_images_onto_page(document, original_page, new_page, image_info_list)
        _draw_text_onto_page(new_page, text_dict["blocks"], replace_text)
    return new_document


def save_modified_document(
    modified_document: Document, original_document_name: str | None
):
    """
    Saves a modified PDF document to disk using a timestamped or derived filename.

    If no original document name is provided, a default name is generated based on
    the current date and time in the format:
    `"Tax Invoice DD_MM_YYYY HH_MM_SS.pdf"`.

    The document is saved with compression enabled (`deflate=True`) to reduce file size,
    and then closed to release resources.

    Args:
        modified_document (fitz.Document): The modified PDF document to be saved.
        original_document_name (str | None): The base name of the original document.
            If `None`, a timestamped filename is generated.

    Raises:
        PDFCreationFailException: If the document cannot be saved due to file I/O errors
            (recommended to add this exception if `save()` can fail in your pipeline).

    Notes:
        - The output path is resolved using `get_output_path()`, which determines where
          the saved file should be written.
        - The function ensures the document is always closed after saving to prevent
          memory leaks or file handle issues.

    Example:
        >>> new_doc = replace_matches_in_pdf(doc, [0], "Tax Invoice")
        >>> save_modified_document(new_doc, "Invoice_1234.pdf")
        # Output saved as: ./output/Invoice_1234.pdf
    """
    if not original_document_name:
        original_document_name = datetime.now().strftime(
            "Tax Invoice %d_%m_%Y %H_%M_%S"
        )

    output_path = get_output_path(
        original_document_name
    )  # pyright: ignore[reportArgumentType]
    modified_document.save(output_path, deflate=True)
    modified_document.close()


if __name__ == "__main__":
    pdf = open_pdf_document("in/19912-October 25.pdf")
    pages_with_credit_notes = get_pages_with_credit_notes(pdf)
    modified_pdf = replace_matches_in_pdf(pdf, pages_with_credit_notes, "CN")
    save_modified_document(modified_pdf, pdf.name)
