# FiscalPDF

FiscalPDF is a lightweight web-based utility used to modify fiscal invoice PDFs by redacting verbose Credit Note references into a standardized short form required for downstream fiscalisation workflows.

Specifically, the tool replaces all verbose credit note occurrences:
```
Example
-------
Credit Note: 12345/678901/23456/A
```
with:
```
CN
```
This allows invoices to be prepared in a consistent format before being submitted to ZIMRA’s fiscalisation system or related compliance processes.

## Prerequisites
1. Docker or Podman

## Installation
```
git clone https://github.com/SageTendo/fiscalpdf/edit/main/README.md
cd fiscalpdf

# Building the Docker or Podman image
# Docker
--------
docker build -t fiscalpdf .

# Podman
--------
podman build -t fiscalpdf .

# Running the Docker or Podman image
# Docker
--------
docker run -p 5000:5000 fiscalpdf

# Podman
--------
podman run -p 5000:5000 fiscalpdf
```

Running the Application
python app.py


Then open:

http://localhost:5000

Limitations

Only performs string-based redaction

Assumes Credit Note text is extractable (not scanned images)

Does not validate fiscal compliance or invoice correctness

Does not generate or manage Credit Notes

Compliance Note

FiscalPDF performs text redaction only.
It does not issue Credit Notes, alter invoice totals, or interact with certified fiscal devices.
Users remain responsible for ensuring compliance with ZIMRA fiscalisation regulations.

Disclaimer

This tool is provided as-is and does not constitute legal, accounting, or tax advice.