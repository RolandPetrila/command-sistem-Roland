"""Shared text extraction from PDF, DOCX, and text files."""

from __future__ import annotations

from pathlib import Path


def extract_text(file_path: str) -> str:
    """Extract text from PDF, DOCX, or text file.

    Lazy-imports fitz/docx to avoid heavy module-level loads.
    """
    p = file_path.lower()
    if p.endswith(".pdf"):
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    elif p.endswith(".docx"):
        from docx import Document as DocxDocument

        doc = DocxDocument(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip()).strip()
    elif p.endswith((".txt", ".md", ".csv", ".json", ".xml", ".html", ".py", ".js")):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    else:
        raise ValueError(f"Tip fisier nesuportat: {Path(file_path).suffix}")
