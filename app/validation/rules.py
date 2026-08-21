from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from dateutil.parser import parse

from app.config import Settings, load_settings
from app.models import AMBIGUOUS, NOT_APPLICABLE, NOT_AVAILABLE, InvoiceRecord


def _decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value.replace(",", "").replace("%", "").strip())
    except (AttributeError, InvalidOperation):
        return None


def validate_invoice(record: InvoiceRecord, settings: Settings | None = None) -> InvoiceRecord:
    settings = settings or load_settings()
    notes: list[str] = []
    for field, label in (("SupplierName", "Supplier name"), ("SupplierAddress", "Supplier address"), ("SupplierGSTIN", "Supplier GSTIN"), ("BFLName", "BFL name"), ("BFLAddress", "BFL address"), ("BFLGSTIN", "BFL GSTIN"), ("Description", "Description"), ("TaxableValue", "Taxable value"), ("TotalValueOfSupply", "Total value of supply"), ("PlaceOfSupply", "Place of supply")):
        if getattr(record, field) in (NOT_AVAILABLE, AMBIGUOUS):
            notes.append(f"{label} {('ambiguous' if getattr(record, field) == AMBIGUOUS else 'missing')}.")
    if record.InvoiceNumber == NOT_AVAILABLE:
        notes.append("Invoice number missing.")
    elif record.InvoiceNumber == AMBIGUOUS:
        notes.append("Invoice number is ambiguous.")
    elif len(record.InvoiceNumber) > 16:
        notes.append("Invoice number exceeds 16 characters.")
    elif not re.fullmatch(r"[A-Za-z0-9/-]+", record.InvoiceNumber):
        notes.append("Invoice number contains prohibited special character.")
    if record.InvoiceDate == NOT_AVAILABLE:
        notes.append("Invoice date missing.")
    else:
        try:
            parse(record.InvoiceDate, dayfirst=False)
        except (TypeError, ValueError, OverflowError):
            notes.append("Invoice date is invalid.")
    if record.SupplierGSTIN != NOT_AVAILABLE and record.SupplierGSTIN != AMBIGUOUS and not re.fullmatch(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]", record.SupplierGSTIN):
        notes.append("Supplier GSTIN appears malformed.")
    if settings.bfl_gstins and record.BFLGSTIN not in settings.bfl_gstins:
        notes.append("BFL GSTIN does not match configured BFL GSTIN.")
    if record.HSNCode in (NOT_AVAILABLE, AMBIGUOUS):
        notes.append(f"HSN/SAC code {('ambiguous' if record.HSNCode == AMBIGUOUS else 'missing')}.")
    if record.QuantityUQC == NOT_AVAILABLE:
        notes.append("Quantity/UQC missing.")
    if record.ReverseCharge == NOT_AVAILABLE:
        notes.append("Reverse charge status unavailable.")
    if record.SignaturePresent != "YES":
        notes.append("Supplier signature not reliably detected.")
    if "QR Not Present" in record.QRIRN:
        notes.append("QR code not present.")
    if "IRN Not Present" in record.QRIRN:
        notes.append("IRN not present.")
    _validate_totals(record, notes)
    record.ValidationNotes = "; ".join(notes) if notes else "VALID - No material validation issues identified."
    return record


def _validate_totals(record: InvoiceRecord, notes: list[str]) -> None:
    taxable = _decimal(record.TaxableValue)
    total = _decimal(record.TotalValueOfSupply)
    tax_values = [_decimal(value) for value in (record.CGSTAmount, record.SGSTAmount, record.IGSTAmount, record.UTGSTAmount, record.CessAmount)]
    tax_values = [value for value in tax_values if value is not None]
    if taxable is None or total is None or not tax_values:
        return
    expected = taxable + sum(tax_values, Decimal("0"))
    difference = abs(expected - total)
    if difference == 0:
        return
    if difference <= Decimal("0.02"):
        notes.append("Total value differs by a reasonable rounding amount.")
    else:
        notes.append("Taxable value plus applicable taxes does not reconcile to total value of supply.")
