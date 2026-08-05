# =============================================================================
# 이 파일의 책임: OCR 비교 전용 서비스(app/ocr_compare_main.py)가 사용할
#   Depends() 조립을 담당한다. Tesseract/EasyOCR(+PyTorch)처럼 무거운 의존성을
#   메인 API(app/dependencies.py)와 분리된 이 모듈에만 두는 게 핵심이다 —
#   메인 API의 라우터들은 이 파일을 아무도 import하지 않으므로, easyocr/
#   pytesseract 패키지 자체가 메인 API 프로세스에는 전혀 로드되지 않는다.
# 다른 파일과의 관계: api/routes/ocr_compare_router.py가 get_ocr_compare_service()를
#   Depends로 가져다 쓴다. get_ocr_extractor()만 app/dependencies.py 것을 그대로
#   재사용한다 — 프로세스가 다르므로 PaddleOCR 인스턴스는 메인 API와 공유되지
#   않고 이 프로세스 안에서 독립적으로 하나 더 만들어진다(격리가 목적이므로 의도된 것).
# =============================================================================

from functools import lru_cache

from fastapi import Depends

from app.dependencies import get_ocr_extractor
from app.extractors.easyocr_extractor import EasyOcrExtractor
from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.tesseract_extractor import TesseractExtractor
from app.services.ocr_compare_service import OcrCompareService


@lru_cache
def get_tesseract_extractor() -> TesseractExtractor:
    return TesseractExtractor()


@lru_cache
def get_easyocr_extractor() -> EasyOcrExtractor:
    return EasyOcrExtractor()


def get_ocr_compare_service(
    paddle_extractor: OcrExtractor = Depends(get_ocr_extractor),
    tesseract_extractor: TesseractExtractor = Depends(get_tesseract_extractor),
    easyocr_extractor: EasyOcrExtractor = Depends(get_easyocr_extractor),
) -> OcrCompareService:
    return OcrCompareService(paddle_extractor, tesseract_extractor, easyocr_extractor)
