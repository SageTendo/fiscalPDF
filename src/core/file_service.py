from datetime import datetime, timedelta
import os
import sys
from threading import Thread
from time import sleep

from src.core.error import (
    NothingToModifyException,
    PDFCreationFailException,
    PathNotFoundException,
    PathNotPDFFileException,
)
from src.core.pdf_service import (
    get_pages_with_credit_notes,
    open_pdf_document,
    replace_matches_in_pdf,
    save_modified_document,
)


class FileService:
    def __init__(self, input_dir, output_dir):
        self.PLATFORM = sys.platform
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.file_watch_thread = Thread(target=self.__stale_file_watcher, daemon=True)
        self.SLEEP_TIME = 60 * 5  # 5 minutes
        self.running = False

    def __is_file_older_than_x_days(self, file, days):
        modification_time = file.stat().st_mtime
        cutoff_time = datetime.now() - timedelta(days=days)
        return modification_time < cutoff_time.timestamp()

    def __stale_file_watcher(self):
        while True:
            self.handle_old_files()
            sleep(self.SLEEP_TIME)

    def handle_old_files(self):
        for file in self.output_dir.iterdir():
            if file.is_file() and file.suffix == ".pdf":
                if self.__is_file_older_than_x_days(file, days=30):
                    try:
                        os.remove(file)
                    except OSError:
                        # TODO: Log error
                        pass

    def handle_file_processing(self, file_path):
        """
        This function handles the processing of a single PDF file.
        It opens the file, redacts credit note information, and saves the modified file.

        Args:
            file_path (str): The path to the PDF file to process.

        Returns:
            Optional[str]: An error message if the processing fails, otherwise None.
        """
        try:
            with open_pdf_document(file_path) as document:
                credit_notes_pages = get_pages_with_credit_notes(document)
                modified_document = replace_matches_in_pdf(document, credit_notes_pages)
                save_modified_document(modified_document, document.name)
        except (
            PathNotFoundException,
            PathNotPDFFileException,
            NothingToModifyException,
            PDFCreationFailException,
        ) as err:
            return str(err)
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                # TODO: Log error
                pass

    def handle_open(self, file=None):
        """
        This function handles file opening for different platforms.
        If no file is provided, it defaults to opening the output directory.
        """
        if not file:
            file = self.output_dir

        match self.PLATFORM:
            case "win32":
                os.startfile(file)  # pyright: ignore[reportAttributeAccessIssue]
            case "linux" | "darwin":
                os.system(f'xdg-open "{file}"')
            case _:
                raise NotImplementedError(f"Platform {self.PLATFORM} not supported.")

    def handle_delete(self, file):
        if file and file.is_file() and file.suffix == ".pdf":
            os.remove(file)

    def get_input_dir(self):
        return self.input_dir

    def get_output_dir(self):
        return self.output_dir

    def run(self):
        if not self.running:
            self.file_watch_thread.start()
            self.running = True
