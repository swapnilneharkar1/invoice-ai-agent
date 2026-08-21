from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass

from app.config import Settings, load_settings
from app.models import AMBIGUOUS, NOT_APPLICABLE, NOT_AVAILABLE, InvoiceRecord

LOGGER = logging.getLogger(__name__)
GSTIN_RE = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")


@dataclass
class DocumentContent:
    text: str
    qr_value: str | None = None
    qr_visible: bool = False
    pages: int = 1


def _ocr_image(image: object, language: str) -> str:
    try:
        import pytesseract
        return pytesseract.image_to_string(image, lang=language)
    except Exception as exc:
        LOGGER.warning("OCR failed: %s", exc)
        return ""


def load_document(filename: str, data: bytes, settings: Settings | None = None) -> DocumentContent:
    settings = settings or load_settings()
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        try:
            import fitz
            document = fitz.open(stream=data, filetype="pdf")
            if document.page_count == 0:
                raise ValueError("PDF contains no pages")
            text_parts: list[str] = []
            qr_values: list[str] = []
            qr_visible = False
            for page in document:
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(page_text)
                else:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    from PIL import Image
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    text_parts.append(_ocr_image(image, settings.ocr_language))
                qr_value, found = _read_qr(page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False))
                qr_visible = qr_visible or found
                if qr_value:
                    qr_values.append(qr_value)
            return DocumentContent("\n".join(text_parts), qr_values[0] if qr_values else None, qr_visible, document.page_count)
        except Exception as exc:
            raise ValueError(f"Unable to read PDF: {exc}") from exc
    try:
        from PIL import Image
        image = Image.open(io.BytesIO(data))
        qr_value, qr_visible = _read_qr(image)
        return DocumentContent(_ocr_image(image, settings.ocr_language), qr_value, qr_visible)
    except Exception as exc:
        raise ValueError(f"Unable to read image: {exc}") from exc


def _read_qr(image: object) -> tuple[str | None, bool]:
    try:
        import cv2
        import numpy as np
        if hasattr(image, "tobytes"):
            if hasattr(image, "samples"):
                array = np.frombuffer(image.samples, dtype=np.uint8).reshape(image.height, image.width, image.n)
            else:
                array = np.array(image)
        else:
            return None, False
        value, points, _ = cv2.QRCodeDetector().detectAndDecode(array)
        return (value or None), points is not None
    except Exception:
        return None, False


def _label_value(text: str, labels: tuple[str, ...]) -> str:
    pattern = r"(?:" + "|".join(re.escape(label) for label in labels) + r")\s*[:#-]?\s*(.+)"
    values = [match.group(1).strip() for match in re.finditer(pattern, text, re.IGNORECASE)]
    values = [value for value in values if value]
    if not values:
        return NOT_AVAILABLE
    unique = list(dict.fromkeys(values))
    return unique[0] if len(unique) == 1 else AMBIGUOUS


def _amount(text: str, labels: tuple[str, ...]) -> str:
    value = _label_value(text, labels)
    match = re.search(r"[-+]?[\d,]+(?:\.\d{1,2})?", value) if value != NOT_AVAILABLE else None
    return match.group(0).replace(",", "") if match else value


def extract_invoice(filename: str, content: DocumentContent, settings: Settings | None = None) -> InvoiceRecord:
    settings = settings or load_settings()
    text = content.text
    gstins = GSTIN_RE.findall(text.upper())
    supplier_gstin = gstins[0] if gstins else NOT_AVAILABLE
    bfl_gstin = next((item for item in gstins if item in settings.bfl_gstins), NOT_AVAILABLE)
    if len(gstins) > 1 and bfl_gstin == NOT_AVAILABLE:
        supplier_gstin = AMBIGUOUS
    record = InvoiceRecord(
        FileName=filename,
        InvoiceNumber=_label_value(text, ("Invoice Number", "Invoice No", "Invoice #")),
        SupplierName=_label_value(text, ("Supplier Name", "Vendor Name", "Seller Name")),
        SupplierAddress=_label_value(text, ("Supplier Address", "Vendor Address", "Seller Address")),
        SupplierGSTIN=supplier_gstin,
        InvoiceDate=_label_value(text, ("Invoice Date", "Date of Invoice")),
        BFLName=_label_value(text, ("Bill To", "Customer Name", "BFL Name")),
        BFLAddress=_label_value(text, ("Bill To Address", "Customer Address", "BFL Address")),
        BFLGSTIN=bfl_gstin,
        HSNCode=_label_value(text, ("HSN/SAC", "HSN Code", "SAC Code")),
        Description=_label_value(text, ("Description", "Particulars", "Service Description")),
        QuantityUQC=_label_value(text, ("Quantity/UQC", "Quantity", "Qty")),
        TaxableValue=_amount(text, ("Taxable Value", "Taxable Amount")),
        TotalValueOfSupply=_amount(text, ("Total Value of Supply", "Total Supply Value")),
        PlaceOfSupply=_label_value(text, ("Place of Supply", "POS")),
        ReverseCharge=_reverse_charge(text),
        SignaturePresent=_signature(text),
        QRIRN=_qr_irn(text, content),
        CGSTRate=_rate(text, ("CGST",)), CGSTAmount=_amount(text, ("CGST Amount", "CGST")),
        SGSTRate=_rate(text, ("SGST",)), SGSTAmount=_amount(text, ("SGST Amount", "SGST")),
        IGSTRate=_rate(text, ("IGST",)), IGSTAmount=_amount(text, ("IGST Amount", "IGST")),
        UTGSTRate=_rate(text, ("UTGST",)), UTGSTAmount=_amount(text, ("UTGST Amount", "UTGST")),
        CessRate=_rate(text, ("Cess",)), CessAmount=_amount(text, ("Cess Amount", "Cess")),
        TotalTaxAmount=_amount(text, ("Total Tax", "Total GST", "Tax Amount")),
    )
    return record


def _rate(text: str, labels: tuple[str, ...]) -> str:
    match = re.search(r"(?:" + "|".join(labels) + r").{0,30}?(\d+(?:\.\d+)?\s*%)", text, re.IGNORECASE)
    return match.group(1).replace(" ", "") if match else NOT_APPLICABLE


def _reverse_charge(text: str) -> str:
    match = re.search(r"(?:reverse charge|RCM).{0,20}\b(yes|no)\b", text, re.IGNORECASE)
    return match.group(1).upper() if match else NOT_AVAILABLE


def _signature(text: str) -> str:
    return "YES" if re.search(r"digital signature|electronically signed|signed by", text, re.IGNORECASE) else "Not Clearly Visible"


def _qr_irn(text: str, content: DocumentContent) -> str:
    irn = re.search(r"\b[0-9a-f]{64}\b", text, re.IGNORECASE)
    qr = "Present" if content.qr_visible else "Not Present"
    irn_status = irn.group(0) if irn else ("Present" if content.qr_value else "Not Present")
    return f"QR {qr}; IRN {irn_status}"
