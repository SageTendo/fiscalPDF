class NothingToModifyException(Exception):
    def __init__(self, doc_name: str):
        super().__init__(f"No changes to make to the provided PDF file: {doc_name}")


class FailedToExtractCreditNotesException(Exception):
    def __init__(self, doc_name: str):
        super().__init__(
            f"Failed to extract credit notes from the provided PDF file: {doc_name}"
        )


class PathNotFoundException(Exception):
    def __init__(self, path):
        super().__init__(f"Path {path} does not exist.")


class PathNotPDFFileException(Exception):
    def __init__(self, path):
        super().__init__(f"Path {path} is not a PDF file.")
