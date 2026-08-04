from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError
from app.dependencies import get_ocr_compare_service
from app.schemas.ocr_compare import OcrCompareResponse, OcrEngineResult
from app.services.ocr_compare_image_loader import ALLOWED_EXTENSIONS, load_comparison_image
from app.services.ocr_compare_service import OcrCompareService

router = APIRouter(prefix="/api", tags=["ocr-compare"])


@router.post("/ocr-compare", response_model=OcrCompareResponse)
def compare_ocr(
    file: UploadFile = File(...),
    service: OcrCompareService = Depends(get_ocr_compare_service),
) -> OcrCompareResponse:
    if not file.filename:
        raise BusinessError(ErrorCode.INVALID_FILE_TYPE, detail="파일명이 필요합니다.")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise BusinessError(
            ErrorCode.INVALID_FILE_TYPE,
            detail=(
                "PNG, JPG, JPEG, BMP, TIF, TIFF, WEBP, GIF 이미지 또는 "
                "PDF, DOCX, HWPX 문서 파일만 업로드할 수 있습니다."
            ),
        )

    content = file.file.read(settings.max_file_size_bytes + 1)

    if len(content) > settings.max_file_size_bytes:
        raise BusinessError(
            ErrorCode.FILE_TOO_LARGE,
            detail=f"파일은 최대 {settings.MAX_FILE_SIZE_MB}MB까지 업로드할 수 있습니다.",
        )

    if not content:
        raise BusinessError(ErrorCode.EXTRACTION_FAILED, detail="빈 파일은 업로드할 수 없습니다.")

    image = load_comparison_image(extension, content)

    results = service.compare(image)

    return OcrCompareResponse(
        paddle=OcrEngineResult.model_validate(results["paddle"]),
        tesseract=OcrEngineResult.model_validate(results["tesseract"]),
        easyocr=OcrEngineResult.model_validate(results["easyocr"]),
    )
