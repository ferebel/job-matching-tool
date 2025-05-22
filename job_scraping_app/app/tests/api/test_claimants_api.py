import pytest
from httpx import AsyncClient # test_client fixture from conftest.py will provide this
from sqlalchemy.orm import Session
from app.models.claimant import SQLClaimant, SQLClaimantDocument, ClaimantCreate # Pydantic model for creation payload
from app.core.config import settings # For potential direct DB checks or config values
import io # For creating dummy file content for uploads

# PyPDF2 and python-docx are needed to create realistic file content for testing document parsing
try:
    from PyPDF2 import PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


# Note: The test_client fixture is defined in conftest.py and handles DB setup/teardown
# and overriding the get_db dependency.

@pytest.mark.asyncio
async def test_create_new_claimant_success(test_client: AsyncClient, test_db_session: Session):
    payload = {"name": "John Doe", "email": "john.doe@example.com", "phone_number": "1234567890", "notes": "Initial notes"}
    response = await test_client.post("/api/v1/claimants/", json=payload)
    
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == payload["name"]
    assert response_data["email"] == payload["email"]
    assert "id" in response_data
    assert "created_at" in response_data
    assert "updated_at" in response_data

    # Verify data in the test database
    db_claimant = test_db_session.query(SQLClaimant).filter(SQLClaimant.id == response_data["id"]).first()
    assert db_claimant is not None
    assert db_claimant.name == payload["name"]
    assert db_claimant.email == payload["email"]
    assert db_claimant.phone_number == payload["phone_number"]
    assert db_claimant.notes == payload["notes"]

@pytest.mark.asyncio
async def test_create_new_claimant_invalid_payload(test_client: AsyncClient):
    payload = {"name": "Missing Email"}  # Email is required
    response = await test_client.post("/api/v1/claimants/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity for Pydantic validation error

@pytest.mark.asyncio
async def test_read_claimant_success(test_client: AsyncClient, test_db_session: Session):
    # First, create a claimant in the test database directly
    claimant_data = ClaimantCreate(name="Jane Read", email="jane.read@example.com", notes="To be read")
    db_claimant = SQLClaimant(
        name=claimant_data.name, 
        email=claimant_data.email,
        notes=claimant_data.notes
    )
    test_db_session.add(db_claimant)
    test_db_session.commit()
    test_db_session.refresh(db_claimant)
    
    claimant_id = db_claimant.id
    response = await test_client.get(f"/api/v1/claimants/{claimant_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == claimant_id
    assert response_data["name"] == claimant_data.name
    assert response_data["email"] == claimant_data.email
    assert response_data["notes"] == claimant_data.notes

@pytest.mark.asyncio
async def test_read_claimant_not_found(test_client: AsyncClient):
    non_existent_id = 99999
    response = await test_client.get(f"/api/v1/claimants/{non_existent_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_upload_claimant_document_success_pdf(test_client: AsyncClient, test_db_session: Session):
    if not PYPDF2_AVAILABLE:
        pytest.skip("PyPDF2 not installed, skipping PDF upload test.")

    # 1. Create a claimant first
    claimant_data = ClaimantCreate(name="Doc Owner", email="doc.owner@example.com")
    db_claimant = SQLClaimant(name=claimant_data.name, email=claimant_data.email)
    test_db_session.add(db_claimant)
    test_db_session.commit()
    test_db_session.refresh(db_claimant)
    claimant_id = db_claimant.id

    # 2. Prepare dummy PDF content
    pdf_content_bytes = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=210, height=297) # A4 size
    # For a real test of text extraction, add text here using a library like reportlab
    # or use a pre-made PDF with known text.
    # For this example, we'll assume extract_text_from_document handles it.
    # If extract_text_from_document is mocked or the PDF is blank, raw_text_content will be empty.
    writer.write(pdf_content_bytes)
    pdf_content_bytes.seek(0)
    
    # 3. Make POST request
    files = {"file": ("test_cv.pdf", pdf_content_bytes, "application/pdf")}
    data = {"document_type": "CV"}
    response = await test_client.post(f"/api/v1/claimants/{claimant_id}/documents/", files=files, data=data)

    assert response.status_code == 200 # Endpoint uses 200 for successful document upload
    response_data = response.json()
    assert response_data["claimant_id"] == claimant_id
    assert response_data["document_type"] == "CV"
    assert "test_cv.pdf" in response_data["file_path"] # Check if filename is in path
    # Check if raw_text_content exists (might be empty if dummy PDF was blank and no real text added)
    assert "raw_text_content" in response_data 
    # Example: if you added text "Hello PDF" to the PDF:
    # assert "Hello PDF" in response_data["raw_text_content"]

    # 4. Verify document data in the test database
    db_document = test_db_session.query(SQLClaimantDocument).filter(SQLClaimantDocument.id == response_data["id"]).first()
    assert db_document is not None
    assert db_document.claimant_id == claimant_id
    assert db_document.document_type == "CV"
    assert "test_cv.pdf" in db_document.file_path
    assert db_document.raw_text_content is not None # Should exist, even if empty

@pytest.mark.asyncio
async def test_upload_claimant_document_success_docx(test_client: AsyncClient, test_db_session: Session):
    if not DOCX_AVAILABLE:
        pytest.skip("python-docx not installed, skipping DOCX upload test.")

    # 1. Create a claimant
    claimant_data = ClaimantCreate(name="Docx User", email="docx.user@example.com")
    db_claimant = SQLClaimant(name=claimant_data.name, email=claimant_data.email)
    test_db_session.add(db_claimant)
    test_db_session.commit()
    test_db_session.refresh(db_claimant)
    claimant_id = db_claimant.id

    # 2. Prepare dummy DOCX content
    docx_content_bytes = io.BytesIO()
    doc = DocxDocument()
    doc.add_paragraph("This is a test DOCX document for upload.")
    doc.save(docx_content_bytes)
    docx_content_bytes.seek(0)

    # 3. Make POST request
    files = {"file": ("test_cv.docx", docx_content_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"document_type": "CoverLetter"}
    response = await test_client.post(f"/api/v1/claimants/{claimant_id}/documents/", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["claimant_id"] == claimant_id
    assert response_data["document_type"] == "CoverLetter"
    assert "test_cv.docx" in response_data["file_path"]
    assert "This is a test DOCX document for upload." in response_data["raw_text_content"]

    # 4. Verify in DB
    db_document = test_db_session.query(SQLClaimantDocument).filter(SQLClaimantDocument.id == response_data["id"]).first()
    assert db_document is not None
    assert "This is a test DOCX document for upload." in db_document.raw_text_content

@pytest.mark.asyncio
async def test_upload_claimant_document_claimant_not_found(test_client: AsyncClient):
    non_existent_claimant_id = 99998
    files = {"file": ("test_cv.pdf", b"dummy pdf content", "application/pdf")}
    data = {"document_type": "CV"}
    response = await test_client.post(f"/api/v1/claimants/{non_existent_claimant_id}/documents/", files=files, data=data)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Claimant not found for document upload"
