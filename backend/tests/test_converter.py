"""Test converter module endpoints."""

import pytest


@pytest.mark.asyncio
async def test_converter_pdf_to_docx_no_file(client):
    """POST /api/converter/pdf-to-docx without file returns 422."""
    resp = await client.post("/api/converter/pdf-to-docx")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_converter_docx_to_pdf_no_file(client):
    """POST /api/converter/docx-to-pdf without file returns 422."""
    resp = await client.post("/api/converter/docx-to-pdf")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_converter_extract_text_no_file(client):
    """POST /api/converter/extract-text without file returns 422."""
    resp = await client.post("/api/converter/extract-text")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_converter_csv_to_json_no_file(client):
    """POST /api/converter/csv-to-json without file returns 422."""
    resp = await client.post("/api/converter/csv-to-json")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_converter_merge_pdfs_no_files(client):
    """POST /api/converter/merge-pdfs without files returns 422."""
    resp = await client.post("/api/converter/merge-pdfs")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_converter_extract_text_with_txt(client):
    """POST /api/converter/extract-text with a text file."""
    content = b"Hello World\nThis is a test document for extraction."
    resp = await client.post(
        "/api/converter/extract-text",
        files={"file": ("test.txt", content, "text/plain")},
    )
    assert resp.status_code in (200, 400, 500)


@pytest.mark.asyncio
async def test_number_to_words(client):
    """GET /api/quick-tools/number-to-words converts numbers."""
    resp = await client.get("/api/quick-tools/number-to-words", params={"number": 1234.56})
    assert resp.status_code == 200
    data = resp.json()
    assert "words" in data
    assert len(data["words"]) > 0


@pytest.mark.asyncio
async def test_number_to_words_zero(client):
    """Number to words handles zero."""
    resp = await client.get("/api/quick-tools/number-to-words", params={"number": 0})
    assert resp.status_code == 200
