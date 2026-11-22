
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
from ..models.document_version import DocumentVersion
from ..models.user import User

from ..dependencies import (
    get_current_user,
    get_accessible_workspace,
    get_editable_workspace,
)

from ..schemas.document import (
    DocumentResponse,
    DocumentVersionUploadResponse,
)
from ..schemas.document_search import (
    DocumentSearchResponse,
    DocumentSearchResult,
)

from ..services.document_extractor import extract_text
from ..services.document_segment_service import (
    calculate_file_checksum,
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
    current_user: User = Depends(get_current_user),
):

    # Step 1: Verify workspace upload permission
    get_editable_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db,
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
            uploaded_by_id=current_user.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=extension.lstrip("."),
            file_size=file_size,
            status="processed",
            extracted_text=extracted_text,
        )

        db.add(document)
        db.flush()

        # Step 9: Create initial document version and segments
        version, segments = create_document_version_and_segments(
            db=db,
            document=document,
        )

        db.refresh(document)

        print(f"Document uploaded successfully: {document.id}")
        print(f"Document version created: {version.version_number}")
        print(f"Document segments created: {len(segments)}")

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
# UPLOAD NEW DOCUMENT VERSION API
# --------------------------------------------------

@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersionUploadResponse,
)
async def upload_document_version(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Step 1: Find the existing document
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # Step 2: Verify workspace edit permission
    get_editable_workspace(
        workspace_id=document.workspace_id,
        current_user=current_user,
        db=db,
    )

    # Step 3: Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    original_filename = (
        file.filename.replace("\\", "/").split("/")[-1]
    )

    extension = Path(original_filename).suffix.lower()

    # Step 4: Validate file extension
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are allowed.",
        )

    # Step 5: Generate a unique storage filename
    stored_filename = f"{uuid4().hex}{extension}"
    destination = DOCUMENT_STORAGE_DIR / stored_filename

    file_size = 0

    try:

        # Step 6: Save uploaded file in chunks
        with destination.open("wb") as buffer:

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File size must not exceed 10 MB.",
                    )

                buffer.write(chunk)

        # Step 7: Extract text from the new file
        extracted_text = extract_text(
            str(destination),
            extension,
        )

        if not extracted_text or not extracted_text.strip():
            raise ValueError(
                "Document has no extracted text. Cannot generate segments."
            )

        # Step 8: Calculate new file checksum
        checksum = calculate_file_checksum(destination)

        # Step 9: Find the latest existing version
        latest_version = (
            db.query(DocumentVersion)
            .filter(
                DocumentVersion.document_id == document_id
            )
            .order_by(
                DocumentVersion.version_number.desc()
            )
            .first()
        )

        # Step 10: Handle duplicate file uploads
        if latest_version and latest_version.checksum == checksum:

            destination.unlink(missing_ok=True)

            existing_segments = (
                db.query(DocumentVersion)
                .filter(
                    DocumentVersion.id == latest_version.id
                )
                .first()
            )

            from ..models.document_segment import DocumentSegment

            segment_count = (
                db.query(DocumentSegment)
                .filter(
                    DocumentSegment.document_version_id
                    == latest_version.id
                )
                .count()
            )

            return DocumentVersionUploadResponse(
                document_id=document.id,
                version_id=latest_version.id,
                version_number=latest_version.version_number,
                is_current=latest_version.is_current,
                checksum=latest_version.checksum,
                segments_created=segment_count,
                message="This file already exists as the latest document version.",
            )

        # Step 11: Update document metadata for the new version
        # Previous version files and records are preserved.
        document.original_filename = original_filename
        document.stored_filename = stored_filename
        document.file_type = extension.lstrip(".")
        document.file_size = file_size
        document.extracted_text = extracted_text
        document.status = "processed"

        db.flush()

        # Step 12: Create new version and its segments
        version, segments = create_document_version_and_segments(
            db=db,
            document=document,
        )

        print(f"New document version created: {version.version_number}")
        print(f"Document ID: {document.id}")
        print(f"Segments created: {len(segments)}")

        return DocumentVersionUploadResponse(
            document_id=document.id,
            version_id=version.id,
            version_number=version.version_number,
            is_current=version.is_current,
            checksum=version.checksum,
            segments_created=len(segments),
            message="New document version uploaded successfully.",
        )

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

        print("Document version upload error:", error)

        raise HTTPException(
            status_code=500,
            detail="Document version upload failed.",
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
    current_user: User = Depends(get_current_user),
):

    # Step 1: Verify workspace access
    get_accessible_workspace(
        workspace_id=workspace_id,
        current_user=current_user,
        db=db,
    )

    # Step 2: Validate search query
    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty.",
        )

    # Step 3: Validate result limit
    if limit < 1 or limit > 50:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 50.",
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
