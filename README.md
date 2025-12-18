
# FiscalPDF
**FiscalPDF** is a lightweight utility designed to preprocess fiscal invoice PDFs by redacting verbose **Credit Note references** into a standardized form before submission to **ZIMRA’s fiscalisation system**.

It was originally created to automate a repetitive internal workflow. Certain enterprise systems generate invoices with verbose Credit Note references, e.g., `Credit Note: 12345/123456/12345/C`, which are not processed by ZIMRA's systems. These references contain internal information that is unnecessary for fiscalisation and must therefore be reduced to `CN` for the invoice to be accepted.

This tool automates that redaction process, removing the need for manual PDF editing while preserving the original invoice layout.


## Features
- Web-based interface and a desktop application variant (Linux & Windows)
- Batch PDF processing
- Automatic detection and redaction of Credit Note references
- Preserves original invoice layout
- Produces fiscalisation-ready PDFs

## How It Works (High-Level)
1. Upload one or more invoice PDFs
2. FiscalPDF scans each document for Credit Note references
3. All detected verbose references are redacted and replaced with `CN`
4. Modified PDFs are generated and ready for fiscalisation

## Building the Desktop Application
FiscalPDF can be packaged as a standalone executable using **PyInstaller**.
This will generate a standalone executable in the `dist/` directory.
### Linux Executable
```bash
git clone https://github.com/SageTendo/fiscalpdf.git
cd fiscalpdf
chmod +x build.sh
./build.sh
```
  
### Windows Executable (via WINE on Linux)
#### Prerequisites
-   WINE
-   Python 3.10 installed inside the WINE environment
-   PyInstaller installed in the Windows Python environment
```bash
git clone https://github.com/SageTendo/fiscalpdf.git
cd fiscalpdf
chmod +x wine-build.sh
./wine-build.sh
```
This allows building a Windows `.exe` from a Linux environment.

## Running the Application
### From Source (Development Mode)
#### Using Pipenv
```bash
# Desktop App
pipenv run python -m src.main

# Web App
pipenv run python -m src.main --web
```
#### Using Pip + Virtualenv
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

# Desktop App
pipenv run python -m src.main

# Web App
pipenv run python -m src.main --web
```
  
### From Executable
#### Linux
```bash
./FiscalPDF
```
#### Windows
Launch `FiscalPDF.exe` like any standard Windows application.

## Disclaimer
1. FiscalPDF was **developed for internal/domain specific use**, and is only public for demonstration purposes.
2. FiscalPDF performs **text redaction and replacement only**. It does **not** perform fiscalisation, validation, or submission to ZIMRA systems.
3. Always verify modified invoices before official submission.