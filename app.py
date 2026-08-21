from __future__ import annotations

import logging

import streamlit as st

from app.exporter import create_excel
from app.processor import process_invoice

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="BFL GST Invoice Validator", page_icon=":page_facing_up", layout="wide")
st.title("BFL GST Invoice Validator")
st.caption("Extract, validate, and export GST invoice information.")

uploads = st.file_uploader("Upload invoice PDF or image files", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"], accept_multiple_files=True)
if uploads:
    st.write(f"Uploaded files: {len(uploads)}")
    st.dataframe({"FileName": [item.name for item in uploads]}, use_container_width=True, hide_index=True)

if st.button("Validate Invoices", type="primary", disabled=not uploads):
    records = []
    progress = st.progress(0, text="Starting validation")
    for index, upload in enumerate(uploads):
        progress.progress(index / len(uploads), text=f"Processing {upload.name}")
        records.append(process_invoice(upload.name, upload.getvalue()))
    progress.progress(1.0, text="Validation complete")
    st.session_state["records"] = records

records = st.session_state.get("records")
if records:
    st.subheader("Validation results")
    st.dataframe([record.as_row() for record in records], use_container_width=True, hide_index=True)
    st.download_button("Download Excel output", create_excel(records), "bfl_invoice_validation.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
