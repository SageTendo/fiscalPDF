import os
import re
from pathlib import Path
from unittest import TestCase
from parameterized import parameterized

from src.lib.pdf_service import (
    CREDIT_NOTE_PATTERN,
    get_pages_with_credit_notes,
    open_pdf_document,
    replace_matches_in_pdf,
)

TEST_PATH = Path(__file__).parent
TEST_INPUT_DIR = TEST_PATH.joinpath("in")
TEST_OUTPUT_DIR = TEST_PATH.joinpath("out")


def get_input_files():
    return list(
        filter(
            lambda x: TEST_INPUT_DIR.joinpath(x).is_file(), os.listdir(TEST_INPUT_DIR)
        )
    )

class TestPDF(TestCase):
    @parameterized.expand([(file,) for file in get_input_files()])
    def test_open_document(self, file):
        filepath: Path = TEST_INPUT_DIR / file
        open_pdf_document(filepath.as_posix())

    @parameterized.expand([(file,) for file in get_input_files()])
    def test_get_pages_with_credit_notes(self, file):
        doc = open_pdf_document((TEST_INPUT_DIR / file).as_posix())
        pages = get_pages_with_credit_notes(doc)
        self.assertEqual(pages, [0])

    @parameterized.expand([(file,) for file in get_input_files()])
    def test_replace_matches_in_pdf(self, file):
        doc = open_pdf_document((TEST_INPUT_DIR / file).as_posix())
        pages = get_pages_with_credit_notes(doc)
        processed_doc = replace_matches_in_pdf(doc, pages, "CN")

        expected = ""
        for page_num in pages:
            page = doc.load_page(page_num)
            text: str = page.get_text()  # type: ignore
            expected += re.sub(CREDIT_NOTE_PATTERN, "CN", text, flags=re.IGNORECASE)
        expected = re.sub(r"\s+", " ", expected)

        actual = ""
        for page_num in pages:
            page = processed_doc.load_page(page_num)
            text = page.get_text()  # type: ignore
            actual += re.sub(r"\s+", " ", text)
        self.assertEqual(expected, actual)
