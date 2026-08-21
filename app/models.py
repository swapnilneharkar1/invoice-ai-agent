from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

NOT_AVAILABLE = "Not Available"
NOT_APPLICABLE = "Not Applicable"
AMBIGUOUS = "Ambiguous"

OUTPUT_COLUMNS = [
    "FileName", "InvoiceNumber", "SupplierName", "SupplierAddress", "SupplierGSTIN",
    "InvoiceDate", "BFLName", "BFLAddress", "BFLGSTIN", "HSNCode", "Description",
    "QuantityUQC", "TaxableValue", "TotalValueOfSupply", "PlaceOfSupply", "ReverseCharge",
    "SignaturePresent", "QRIRN", "CGSTRate", "CGSTAmount", "SGSTRate", "SGSTAmount",
    "IGSTRate", "IGSTAmount", "UTGSTRate", "UTGSTAmount", "CessRate", "CessAmount",
    "TotalTaxAmount", "ValidationNotes",
]


class InvoiceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    FileName: str = NOT_AVAILABLE
    InvoiceNumber: str = NOT_AVAILABLE
    SupplierName: str = NOT_AVAILABLE
    SupplierAddress: str = NOT_AVAILABLE
    SupplierGSTIN: str = NOT_AVAILABLE
    InvoiceDate: str = NOT_AVAILABLE
    BFLName: str = NOT_AVAILABLE
    BFLAddress: str = NOT_AVAILABLE
    BFLGSTIN: str = NOT_AVAILABLE
    HSNCode: str = NOT_AVAILABLE
    Description: str = NOT_AVAILABLE
    QuantityUQC: str = NOT_AVAILABLE
    TaxableValue: str = NOT_AVAILABLE
    TotalValueOfSupply: str = NOT_AVAILABLE
    PlaceOfSupply: str = NOT_AVAILABLE
    ReverseCharge: str = NOT_AVAILABLE
    SignaturePresent: str = "Not Clearly Visible"
    QRIRN: str = NOT_AVAILABLE
    CGSTRate: str = NOT_APPLICABLE
    CGSTAmount: str = NOT_APPLICABLE
    SGSTRate: str = NOT_APPLICABLE
    SGSTAmount: str = NOT_APPLICABLE
    IGSTRate: str = NOT_APPLICABLE
    IGSTAmount: str = NOT_APPLICABLE
    UTGSTRate: str = NOT_APPLICABLE
    UTGSTAmount: str = NOT_APPLICABLE
    CessRate: str = NOT_APPLICABLE
    CessAmount: str = NOT_APPLICABLE
    TotalTaxAmount: str = NOT_AVAILABLE
    ValidationNotes: str = ""

    def as_row(self) -> dict[str, str]:
        return self.model_dump(include=set(OUTPUT_COLUMNS))
