
from pathlib import Path

import pymupdf
from docx import Document


def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF document."""

    extracted_pages = []

    try:
        with pymupdf.open(file_path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text("text").strip()

                if page_text:
                    extracted_pages.append(
                        f"[Page {page_number}]\n{page_text}"
                    )

    except Exception as error:
        raise ValueError(f"Could not extract PDF text: {error}")

    return "\n\n".join(extracted_pages)


def extract_docx_text(file_path: str) -> str:
    """Extract paragraphs and tables from a DOCX document."""

    try:
        document = Document(file_path)
        content = []

        # Extract paragraphs
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                content.append(text)

        # Extract tables
        for table in document.tables:
            for row in table.rows:
                row_text = [
                    cell.text.strip()
                    for cell in row.cells
                    if cell.text.strip()
                ]

                if row_text:
                    content.append(" | ".join(row_text))

        return "\n\n".join(content)

    except Exception as error:
        raise ValueError(f"Could not extract DOCX text: {error}")


def extract_txt_text(file_path: str) -> str:
    """Extract text from a TXT document."""

    try:
        return Path(file_path).read_text(
            encoding="utf-8-sig"
        ).strip()

    except UnicodeDecodeError as error:
        raise ValueError(
            "TXT file must use UTF-8 text encoding."
        ) from error

    except Exception as error:
        raise ValueError(f"Could not extract TXT text: {error}")


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text based on the document file type."""

    file_type = file_type.lower().lstrip(".")

    if file_type == "pdf":
        extracted_text = extract_pdf_text(file_path)

    elif file_type == "docx":
        extracted_text = extract_docx_text(file_path)

    elif file_type == "txt":
        extracted_text = extract_txt_text(file_path)

    else:
        raise ValueError(
            f"Unsupported document format: {file_type}"
        )

    if not extracted_text.strip():
        raise ValueError(
            "The document contains no extractable text."
        )

    return extracted_text
