from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError
from app.ocr_compare_dependencies import get_ocr_compare_service
from app.schemas.ocr_compare import OcrCompareResponse, OcrEngineResult
from app.services.ocr_compare_image_loader import ALLOWED_EXTENSIONS, load_comparison_image
from app.services.ocr_compare_service import OcrCompareService
from app.services.ocr_ground_truth import parse_ground_truth_text

router = APIRouter(prefix="/api", tags=["ocr-compare"])


@router.post("/ocr-compare", response_model=OcrCompareResponse)
def compare_ocr(
    file: UploadFile = File(...),
    # 정답 데이터(LabelMe 형식 JSON). 주면 confidence 대신 실제 정확도(CER 기반)를 계산한다.
    ground_truth: UploadFile | None = File(None),
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

    reference_text = None
    if ground_truth is not None and ground_truth.filename:
        ground_truth_content = ground_truth.file.read(settings.max_file_size_bytes + 1)
        reference_text = parse_ground_truth_text(ground_truth_content)

    image = load_comparison_image(extension, content)

    results = service.compare(image, reference_text)

    return OcrCompareResponse(
        paddle=OcrEngineResult.model_validate(results["paddle"]),
        tesseract=OcrEngineResult.model_validate(results["tesseract"]),
        easyocr=OcrEngineResult.model_validate(results["easyocr"]),
    )
