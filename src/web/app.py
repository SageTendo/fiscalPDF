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

from config import INPUT_DIR, OUTPUT_DIR
from src.lib.file_service import FileService

app = Flask(__name__)
app.secret_key = os.urandom(24)
file_service: FileService = FileService(INPUT_DIR, OUTPUT_DIR)


def save_uploaded_file(file):
    save_path = INPUT_DIR.joinpath(file.filename)
    f = open(save_path, "wb")
    f.write(file.stream.read())
    f.close()
    return save_path


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

    uploaded_file = save_uploaded_file(file).as_posix()
    error = file_service.handle_file_processing(uploaded_file)
    if error:
        flash(error)
    return redirect(url_for("home"))


@app.post("/bulk-upload")
def bulk_upload():
    files = request.files.getlist("files")
    if not files:
        flash("No files uploaded")
        return redirect(url_for("home"))

    for file in files:
        uploaded_file = save_uploaded_file(file).as_posix()
        error = file_service.handle_file_processing(uploaded_file)
        if error:
            flash(error)
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


def main():
    from waitress import serve

    serve(app, host="0.0.0.0", port=5000)
