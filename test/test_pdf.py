import os
import re
from pathlib import Path
from unittest import TestCase

from pdf import (
    CREDIT_NOTE_PATTERN,
    get_output_path,
    get_pages_with_credit_notes,
    open_pdf_document,
    replace_matches_in_pdf,
)

TEST_PATH = Path(__file__).parent
TEST_INPUT_DIR = TEST_PATH.joinpath("in")


def get_input_files():
    return list(
        filter(
            lambda x: TEST_INPUT_DIR.joinpath(x).is_file(), os.listdir(TEST_INPUT_DIR)
        )
    )


class TestPDF(TestCase):
    def __init__(self, methodName: str = "runTestPDF") -> None:
        super().__init__(methodName)

    def test_open_document(self):
        files = get_input_files()
        for file in files:
            filepath: Path = TEST_INPUT_DIR / file
            open_pdf_document(filepath.as_posix())

    def test_get_pages_with_credit_notes(self):
        files = get_input_files()
        for file in files:
            doc = open_pdf_document((TEST_INPUT_DIR / file).as_posix())
            pages = get_pages_with_credit_notes(doc)
            self.assertEqual(pages, [0])

    def test_replace_matches_in_pdf(self):
        files = get_input_files()
        for file in files:
            doc = open_pdf_document((TEST_INPUT_DIR / file).as_posix())
            pages = get_pages_with_credit_notes(doc)

            expected = ""
            for page_num in pages:
                page = doc.load_page(page_num)
                text: str = page.get_text()  # type: ignore
                expected += re.sub(CREDIT_NOTE_PATTERN, "CN", text, flags=re.IGNORECASE)
            expected = re.sub(r"\s+", " ", expected)

            replace_matches_in_pdf(doc, pages, "CN")
            processed_doc = open_pdf_document(get_output_path(doc.name).as_posix())  # type: ignore
            actual = ""
            for page_num in pages:
                page = processed_doc.load_page(page_num)
                text = page.get_text()  # type: ignore
                actual += re.sub(r"\s+", " ", text)
            assert expected == actual
