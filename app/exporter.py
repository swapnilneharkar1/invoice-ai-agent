from __future__ import annotations

from io import BytesIO

import pandas as pd
from openpyxl.styles import Alignment, Font

from app.models import OUTPUT_COLUMNS, InvoiceRecord


def create_excel(records: list[InvoiceRecord]) -> bytes:
    frame = pd.DataFrame([record.as_row() for record in records], columns=OUTPUT_COLUMNS)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="Invoice Validation")
        worksheet = writer.sheets["Invoice Validation"]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
        for column in worksheet.columns:
            width = min(max(max(len(str(cell.value or "")) for cell in column) + 2, 12), 45)
            worksheet.column_dimensions[column[0].column_letter].width = width
            for cell in column:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
    return output.getvalue()
