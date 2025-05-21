import pytest
from httpx import AsyncClient
from app.main import app  # Your FastAPI app instance
from app.models.claimant import ClaimantRead, ClaimantDocumentRead # Pydantic models
from unittest.mock import patch, MagicMock # For mocking
from datetime import datetime

# Helper to get the base URL for the test client
BASE_URL = "http://test"

@pytest.mark.asyncio
async def test_create_new_claimant_success():
    mock_created_claimant = ClaimantRead(
        id=1,
        name="Test User",
        email="test@example.com",
        phone_number="1234567890",
        notes="Test notes",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    with patch("app.db.crud_claimant.create_claimant", return_value=mock_created_claimant) as mock_create:
        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            payload = {"name": "Test User", "email": "test@example.com", "phone_number": "1234567890", "notes": "Test notes"}
            response = await ac.post("/api/v1/claimants/", json=payload)

        mock_create.assert_called_once()
        assert response.status_code == 201
        response_data = response.json()
        # Compare relevant fields, excluding dynamic ones like created_at/updated_at if they cause issues
        assert response_data["name"] == mock_created_claimant.name
        assert response_data["email"] == mock_created_claimant.email
        assert response_data["id"] == mock_created_claimant.id

@pytest.mark.asyncio
async def test_create_new_claimant_invalid_payload():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        payload = {"name": "Test User"}  # Missing email
        response = await ac.post("/api/v1/claimants/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity for Pydantic validation error

@pytest.mark.asyncio
async def test_read_claimant_success():
    claimant_id = 1
    mock_claimant = ClaimantRead(
        id=claimant_id,
        name="Test User",
        email="test@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    with patch("app.db.crud_claimant.get_claimant", return_value=mock_claimant) as mock_get:
        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            response = await ac.get(f"/api/v1/claimants/{claimant_id}")

        mock_get.assert_called_once_with(db=None, claimant_id=claimant_id) # Ensure db=None is also checked if your Depends is like that
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == mock_claimant.id
        assert response_data["name"] == mock_claimant.name

@pytest.mark.asyncio
async def test_read_claimant_not_found():
    claimant_id = 99
    with patch("app.db.crud_claimant.get_claimant", return_value=None) as mock_get:
        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            response = await ac.get(f"/api/v1/claimants/{claimant_id}")

        mock_get.assert_called_once_with(db=None, claimant_id=claimant_id)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_upload_claimant_document_success():
    claimant_id = 1
    mock_document = ClaimantDocumentRead(
        id=1,
        claimant_id=claimant_id,
        document_type="CV",
        file_path=f"uploads/claimant_{claimant_id}/test_cv.pdf",
        uploaded_at=datetime.utcnow()
    )
    # Mock get_claimant to simulate claimant exists
    mock_claimant = ClaimantRead(id=claimant_id, name="Test User", email="test@example.com", created_at=datetime.utcnow(), updated_at=datetime.utcnow())

    with patch("app.db.crud_claimant.get_claimant", return_value=mock_claimant), \
         patch("app.db.crud_claimant.add_claimant_document", return_value=mock_document) as mock_add_doc:

        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            # Prepare multipart form data
            files = {"file": ("test_cv.pdf", b"dummy content", "application/pdf")}
            data = {"document_type": "CV"}
            response = await ac.post(f"/api/v1/claimants/{claimant_id}/documents/", files=files, data=data)

        # Check that add_claimant_document was called correctly
        # The actual file object will be a SpooledTemporaryFile, so direct comparison is tricky.
        # We can check if it was called and the type of the file argument.
        assert mock_add_doc.call_count == 1
        call_args = mock_add_doc.call_args[1] # Get keyword arguments
        assert call_args['claimant_id'] == claimant_id
        assert call_args['document_type'] == "CV"
        assert hasattr(call_args['file'], 'filename')
        assert call_args['file'].filename == "test_cv.pdf"
        
        assert response.status_code == 200 # As per your current implementation
        response_data = response.json()
        assert response_data["id"] == mock_document.id
        assert response_data["document_type"] == mock_document.document_type
        assert response_data["file_path"] == mock_document.file_path

@pytest.mark.asyncio
async def test_upload_claimant_document_claimant_not_found():
    claimant_id = 99 # Non-existent claimant
    with patch("app.db.crud_claimant.get_claimant", return_value=None) as mock_get_claimant:
        async with AsyncClient(app=app, base_url=BASE_URL) as ac:
            files = {"file": ("test_cv.pdf", b"dummy content", "application/pdf")}
            data = {"document_type": "CV"}
            response = await ac.post(f"/api/v1/claimants/{claimant_id}/documents/", files=files, data=data)

        mock_get_claimant.assert_called_once_with(db=None, claimant_id=claimant_id)
        assert response.status_code == 404
        assert response.json()["detail"] == "Claimant not found for document upload"
