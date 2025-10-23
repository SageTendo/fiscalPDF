import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    flash,
    send_from_directory,
    redirect,
    url_for,
)

from error import (
    NothingToModifyException,
    PDFCreationFailException,
    PathNotFoundException,
    PathNotPDFFileException,
)
from pdf import (
    open_pdf_document,
    get_pages_with_credit_notes,
    replace_matches_in_pdf,
    save_modified_document,
)
from config import INPUT_DIR, OUTPUT_DIR

app = Flask(__name__)
app.secret_key = os.urandom(24)


def save_uploaded_file(file):
    save_path = INPUT_DIR.joinpath(file.filename)
    f = open(save_path, "wb")
    f.write(file.stream.read())
    f.close()
    return save_path


def process_file(file_path):
    try:
        document = open_pdf_document(file_path)
        pages_with_credit_notes = get_pages_with_credit_notes(document)
        modified_document = replace_matches_in_pdf(
            document, pages_with_credit_notes, "CN"
        )
        save_modified_document(modified_document, document.name)
    except (
        PathNotFoundException,
        PathNotPDFFileException,
        NothingToModifyException,
        PDFCreationFailException,
    ) as err:
        flash(err.__str__())
    finally:
        os.remove(file_path)


@app.route("/")
def home():
    processed_files = [
        {
            "name": f.name,
            "date_modified": datetime.fromtimestamp(f.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        for f in OUTPUT_DIR.iterdir()
        if f.is_file() and f.suffix == ".pdf"
    ]
    return render_template("home.html", processed_files=processed_files)


@app.post("/upload")
def upload():
    file = request.files["file"]
    if not file:
        flash("A file is required to upload")
        return redirect(url_for("home"))

    uploaded_file = save_uploaded_file(file)
    process_file(uploaded_file)
    return redirect(url_for("home"))


@app.post("/bulk-upload")
def bulk_upload():
    files = request.files.getlist("files")
    if not files:
        flash("No files uploaded")
        return redirect(url_for("home"))

    for file in files:
        uploaded_file = save_uploaded_file(file)
        process_file(uploaded_file)
    return redirect(url_for("home"))


@app.route("/delete/<filename>")
def delete_file(filename):
    if OUTPUT_DIR.joinpath(filename).exists():
        os.remove(OUTPUT_DIR.joinpath(filename))
    return redirect(url_for("home"))


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


@app.route("/view/<filename>")
def view_pdf(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run()
