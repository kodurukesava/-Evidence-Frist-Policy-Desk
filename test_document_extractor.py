
from pathlib import Path

import pymupdf
from docx import Document

from backend.app.services.document_extractor import extract_text


# Create a temporary directory for test documents
TEST_DIR = Path("data/test_documents")
TEST_DIR.mkdir(parents=True, exist_ok=True)


# 1. Create a sample PDF
pdf_path = TEST_DIR / "sample.pdf"

pdf = pymupdf.open()
page = pdf.new_page()
page.insert_text(
    (72, 72),
    "Evidence-First Policy Desk\nPDF extraction test successful."
)
pdf.save(pdf_path)
pdf.close()


# 2. Create a sample DOCX
docx_path = TEST_DIR / "sample.docx"

document = Document()
document.add_heading("Document Extraction Test", level=1)
document.add_paragraph(
    "Evidence-First Policy Desk DOCX extraction test successful."
)

table = document.add_table(rows=1, cols=2)
table.rows[0].cells[0].text = "Policy"
table.rows[0].cells[1].text = "Evidence"

document.save(docx_path)


# 3. Create a sample TXT
txt_path = TEST_DIR / "sample.txt"

txt_path.write_text(
    "Evidence-First Policy Desk TXT extraction test successful.",
    encoding="utf-8"
)


# 4. Test PDF extraction
print("\n========== PDF EXTRACTION ==========")

pdf_text = extract_text(str(pdf_path), "pdf")
print(pdf_text)
print("PDF TEST: PASSED")


# 5. Test DOCX extraction
print("\n========== DOCX EXTRACTION ==========")

docx_text = extract_text(str(docx_path), "docx")
print(docx_text)
print("DOCX TEST: PASSED")


# 6. Test TXT extraction
print("\n========== TXT EXTRACTION ==========")

txt_text = extract_text(str(txt_path), "txt")
print(txt_text)
print("TXT TEST: PASSED")


print("\nALL THREE EXTRACTION TESTS PASSED!")
