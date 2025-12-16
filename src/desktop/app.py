import os
import tkinter as tk
from tkinter import filedialog, messagebox
from platformdirs import user_documents_dir
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from datetime import datetime

from config import INPUT_DIR, OUTPUT_DIR
from src.lib.file_service import FileService


class FiscalPDFApp(tk.Tk):
    def __init__(self, file_service: FileService):
        super().__init__()
        ttk.Style("cosmo")

        self.title("FiscalPDF")
        self.geometry("1280x768")
        self.resizable(True, True)

        self.file_service = file_service
        self.input_dir = file_service.get_input_dir()
        self.output_dir = file_service.get_output_dir()

        self._ensure_dirs()
        self._build_ui()
        self._refresh_table()
        self.file_service.run()

    # -------------------------
    # UI
    # -------------------------
    def _build_ui(self):
        ttk.Label(
            self,
            text="FiscalPDF",
            font=("", 20, "bold"),
            foreground="#ffffff",
            background="#414850",
            padding=(20, 20, 20, 20),
        ).pack(fill="x")

        ttk.Label(
            self,
            text="Format PDFs for Fiscal Reporting",
            font=("", 20, "bold"),
        ).pack(pady=20)

        container = ttk.Frame(self)
        container.pack(fill="x", padx=30)

        upload_frame = ttk.Frame(container)
        upload_frame.pack(fill="x")
        self._single_upload(upload_frame)
        self._bulk_upload(upload_frame)
        self._output_section()

    def _single_upload(self, parent):
        frame = ttk.Frame(parent, border=10, relief="groove", padding=10)

        ttk.Label(frame, text="Single PDF Upload", font=("", 12, "bold")).pack(pady=10)
        ttk.Label(frame, text="Upload one PDF to process").pack()
        ttk.Button(
            frame,
            text="Select PDF",
            command=self._upload_single,
            bootstyle=(SUCCESS, OUTLINE),
        ).pack(pady=10)
        frame.pack(side="left", expand=True, fill="x", padx=10, pady=10)

    def _bulk_upload(self, parent):
        frame = ttk.Frame(parent, border=10, relief="groove", padding=10)

        ttk.Label(frame, text="Bulk PDF Upload", font=("", 12, "bold")).pack(pady=10)
        ttk.Label(frame, text="Select multiple PDFs to process at once").pack()
        ttk.Button(
            frame,
            text="Select PDFs",
            command=self._upload_bulk,
            bootstyle=(SUCCESS, OUTLINE),
        ).pack(pady=10)
        frame.pack(side="left", expand=True, fill="x", padx=10, pady=10)

    def _output_section(self):
        frame = ttk.Label(self, text="Processed Files")
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        columns = ("name", "date")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)

        self.tree.heading("name", text="File Name")
        self.tree.heading("date", text="Date Modified")

        self.tree.column("name", width=400, stretch=True)
        self.tree.column("date", width=200, stretch=True)

        self.tree.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame, text="View", command=self._view_file, bootstyle="outline-success"
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame,
            text="Open Folder",
            command=self.file_service.handle_open,
            bootstyle="outline-primary",
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Delete", command=self._delete_file, bootstyle="danger"
        ).pack(side="left", padx=5)

    # -------------------------
    # Actions
    # -------------------------
    def _upload_single(self):
        file = filedialog.askopenfilename(
            parent=self,
            title="Select PDF",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=os.getcwd(),
        )
        if file:
            self._process_and_refresh([file])

    def _upload_bulk(self):
        files = filedialog.askopenfilenames(
            parent=self,
            title="Select PDFs",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=os.getcwd(),
        )
        if files:
            self._process_and_refresh(files)

    def _process_and_refresh(self, files):
        try:
            for file in files:
                dest = self.input_dir / os.path.basename(file)
                with open(file, "rb") as src, open(dest, "wb") as dst:
                    dst.write(src.read())

                error = self.file_service.handle_file_processing(dest)
                if error:
                    messagebox.showerror("Error", error)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self._refresh_table()

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for f in self.output_dir.iterdir():
            if f.suffix == ".pdf":
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        f.name,
                        datetime.fromtimestamp(f.stat().st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                )

    def _selected_file(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a file first.")
            return None
        return self.output_dir / self.tree.item(selected[0])["values"][0]

    def _selected_files(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select file(s) first.")
            return None
        return [self.output_dir / self.tree.item(s)["values"][0] for s in selected]

    def _view_file(self):
        file = self._selected_file()
        if not file:
            return
        self.file_service.handle_open(file)

    def _delete_file(self):
        files = self._selected_files()
        if not files:
            return

        response = messagebox.askyesno("Confirm", "Delete selected files?")
        if not response:
            return

        for file in files:
            self.file_service.handle_delete(file)
        self._refresh_table()

    # -------------------------
    # Utils
    # -------------------------
    def _ensure_dirs(self):
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)


def main():
    file_service = FileService(INPUT_DIR, OUTPUT_DIR)
    app = FiscalPDFApp(file_service)
    app.mainloop()
