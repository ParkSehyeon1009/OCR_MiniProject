from fastapi import APIRouter, Depends, File, UploadFile
from starlette import status

from app.dependencies import get_extraction_service
from app.schemas.document import DocumentUploadResponse
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/api", tags=["upload"])


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    service: ExtractionService = Depends(get_extraction_service),
) -> DocumentUploadResponse:
    content = file.file.read()
    document = service.upload_and_extract(file.filename, content)

    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        document_type=document.document_type,
        status=document.status,
        page_count=document.extracted_text.page_count,
        char_count=document.extracted_text.char_count,
        extract_method=document.extracted_text.extract_method,
        created_at=document.created_at,
    )
