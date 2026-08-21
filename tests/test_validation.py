from app.models import InvoiceRecord, NOT_APPLICABLE, NOT_AVAILABLE, OUTPUT_COLUMNS
from app.validation.rules import validate_invoice


def base_record(**changes):
    values = dict(
        FileName="invoice.pdf", InvoiceNumber="INV/001", SupplierName="Supplier",
        SupplierAddress="Supplier address", SupplierGSTIN="27ABCDE1234F1Z5", InvoiceDate="21/08/2026",
        BFLName="Bajaj Finance Limited", BFLAddress="BFL address", BFLGSTIN="27ABCDE1234F1Z5",
        HSNCode="9983", Description="Services", QuantityUQC="1 NOS", TaxableValue="100.00",
        TotalValueOfSupply="118.00", PlaceOfSupply="Maharashtra (27)", ReverseCharge="NO",
        SignaturePresent="YES", QRIRN="QR Present; IRN Present", CGSTRate="9%", CGSTAmount="9.00",
        SGSTRate="9%", SGSTAmount="9.00", TotalTaxAmount="18.00",
    )
    values.update(changes)
    return InvoiceRecord(**values)


def test_valid_invoice_number():
    assert "Invoice number" not in validate_invoice(base_record()).ValidationNotes


def test_invoice_number_over_16_characters():
    assert "exceeds 16" in validate_invoice(base_record(InvoiceNumber="A" * 17)).ValidationNotes


def test_invoice_number_invalid_characters():
    assert "prohibited" in validate_invoice(base_record(InvoiceNumber="INV_001")).ValidationNotes


def test_missing_gstin():
    assert "Supplier GSTIN missing" in validate_invoice(base_record(SupplierGSTIN=NOT_AVAILABLE)).ValidationNotes


def test_missing_invoice_date():
    assert "Invoice date missing" in validate_invoice(base_record(InvoiceDate=NOT_AVAILABLE)).ValidationNotes


def test_missing_hsn():
    assert "HSN/SAC code missing" in validate_invoice(base_record(HSNCode=NOT_AVAILABLE)).ValidationNotes


def test_tax_calculation_mismatch():
    assert "does not reconcile" in validate_invoice(base_record(TotalValueOfSupply="140.00")).ValidationNotes


def test_reverse_charge_unavailable():
    assert "Reverse charge status unavailable" in validate_invoice(base_record(ReverseCharge=NOT_AVAILABLE)).ValidationNotes


def test_qr_irn_missing():
    notes = validate_invoice(base_record(QRIRN="QR Not Present; IRN Not Present")).ValidationNotes
    assert "QR code not present" in notes and "IRN not present" in notes


def test_output_schema_is_exact():
    assert list(base_record().as_row()) == OUTPUT_COLUMNS


def test_multiple_invoices_are_independent():
    first = validate_invoice(base_record(FileName="one.pdf"))
    second = validate_invoice(base_record(FileName="two.pdf", InvoiceNumber="A" * 17))
    assert first.FileName == "one.pdf"
    assert "exceeds 16" in second.ValidationNotes
