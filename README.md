# BFL GST Invoice Validator

Browser-based proof of concept for extracting and validating GST invoice data for Bajaj Finance Limited (BFL), then exporting one validated row per invoice to Excel.

## Features

- Upload one or multiple PDF and image invoices.
- Extract text from digital PDFs and OCR scanned PDFs/images.
- Detect QR codes and readable IRNs when possible.
- Validate required fields, invoice number format, GSTIN shape, tax totals, reverse charge, signature status, and QR/IRN status.
- Continue processing when one invoice fails.
- Export exactly the required 30 columns to `bfl_invoice_validation.xlsx`.

## Installation

Use Python 3.10 or newer:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

OCR requires the Tesseract executable to be installed separately and available on `PATH`. Digital PDFs can still be processed without Tesseract.

## Configuration

No API keys are required. Optional environment variables use pipe-separated values:

```powershell
$env:BFL_NAMES = "Bajaj Finance Limited"
$env:BFL_GSTINS = "27ABCDE1234F1Z5"
$env:BFL_ADDRESSES = "Configured BFL address"
$env:OCR_LANGUAGE = "eng"
```

Never put secrets in source files. A future managed OCR provider can read its credentials from environment variables or a secret manager.

## Run

```powershell
streamlit run app.py
```

Open the displayed local URL, upload invoice files, click **Validate Invoices**, review the results, and download the Excel workbook.

## Tests

```powershell
python -m pytest
```

The tests cover invoice number rules, missing fields, tax reconciliation, reverse charge, QR/IRN status, output schema, and independent processing of multiple invoices.

## Project Structure

- `app.py`: Streamlit browser UI
- `app/processor.py`: per-file fault isolation and orchestration
- `app/extraction/`: PDF/image loading, OCR, QR detection, and field extraction
- `app/validation/`: GST and mathematical validation rules
- `app/models.py`: strict record model and exact output columns
- `app/exporter.py`: formatted Excel generation
- `app/config.py`: environment-based configuration
- `tests/`: unit tests

Extraction is intentionally conservative. Values that cannot be reliably identified are reported as `Not Available`; unresolved candidates are reported as `Ambiguous` and explained in `ValidationNotes`.
