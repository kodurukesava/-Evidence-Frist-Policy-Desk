
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.document import Document
from ..models.workspace import Workspace

from ..schemas.document import DocumentResponse
from ..schemas.document_search import (
    DocumentSearchResponse,
    DocumentSearchResult,
)

from ..services.document_extractor import extract_text
from ..services.document_segment_service import (
    create_document_version_and_segments,
)
from ..services.document_search import search_document_segments


# Create Documents API router
router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Document storage directory
DOCUMENT_STORAGE_DIR = PROJECT_ROOT / "data" / "documents"
DOCUMENT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# Upload restrictions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# --------------------------------------------------
# DOCUMENT UPLOAD API
# --------------------------------------------------

@router.post(
    "/upload/{workspace_id}",
    response_model=DocumentResponse,
)
async def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # Step 1: Check whether workspace exists
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found.",
        )

    # Step 2: Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    original_filename = (
        file.filename.replace("\\", "/").split("/")[-1]
    )

    extension = Path(original_filename).suffix.lower()

    # Step 3: Validate file extension
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are allowed.",
        )

    # Step 4: Generate unique filename
    stored_filename = f"{uuid4().hex}{extension}"
    destination = DOCUMENT_STORAGE_DIR / stored_filename

    file_size = 0

    try:

        # Step 5: Save uploaded file in chunks
        with destination.open("wb") as buffer:

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                file_size += len(chunk)

                # Step 6: Check maximum file size
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File size must not exceed 10 MB.",
                    )

                buffer.write(chunk)

        # Step 7: Extract document text
        extracted_text = extract_text(
            str(destination),
            extension,
        )

        # Step 8: Create document database record
        document = Document(
            workspace_id=workspace_id,
            uploaded_by_id=1,  # Temporary until authentication
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=extension.lstrip("."),
            file_size=file_size,
            status="processed",
            extracted_text=extracted_text,
        )

        db.add(document)

        # Generate document ID without committing yet
        db.flush()

        # Step 9: Automatically create document version
        # and save extracted text chunks into SQLite
        version, segments = create_document_version_and_segments(
            db=db,
            document=document,
        )

        # The segment service commits the transaction.
        db.refresh(document)

        print(
            f"Document uploaded successfully: {document.id}"
        )
        print(
            f"Document version created: {version.version_number}"
        )
        print(
            f"Document segments created: {len(segments)}"
        )

        return document

    except HTTPException:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    except ValueError as error:
        db.rollback()
        destination.unlink(missing_ok=True)

        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except Exception as error:
        db.rollback()
        destination.unlink(missing_ok=True)

        print("Document upload error:", error)

        raise HTTPException(
            status_code=500,
            detail="Document upload failed.",
        )

    finally:
        await file.close()


# --------------------------------------------------
# DOCUMENT SEARCH API
# --------------------------------------------------

@router.get(
    "/search/{workspace_id}",
    response_model=DocumentSearchResponse,
)
def search_documents(
    workspace_id: int,
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):

    # Step 1: Validate search query
    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    # Step 2: Validate result limit
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 50.",
        )

    # Step 3: Check whether workspace exists
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found.",
        )

    try:

        # Step 4: Search document segments using FTS5
        results = search_document_segments(
            db=db,
            workspace_id=workspace_id,
            query=query,
            limit=limit,
        )

        # Step 5: Format search results
        formatted_results = [
            DocumentSearchResult(**result)
            for result in results
        ]

        # Step 6: Return structured response
        return DocumentSearchResponse(
            query=query,
            workspace_id=workspace_id,
            total_results=len(formatted_results),
            results=formatted_results,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
