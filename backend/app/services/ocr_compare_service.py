import time
from dataclasses import dataclass

from PIL import Image

from app.extractors.easyocr_extractor import EasyOcrExtractor
from app.extractors.layout import LayoutElement
from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.tesseract_extractor import TesseractExtractor
from app.services.ocr_ground_truth import compute_accuracy


@dataclass(frozen=True)
class OcrRunResult:
    engine: str
    text: str
    char_count: int
    # 각 엔진이 자체적으로 보고하는 인식 신뢰도(confidence) 평균 (0~100%).
    # 정답 데이터가 없을 때 "정확도" 대용으로만 참고한다.
    avg_confidence: float | None
    elapsed_ms: int
    # 정답 데이터(ground truth)가 함께 주어졌을 때만 채워지는 실제 정확도.
    # CER(문자 오류율) 기반이라 confidence보다 신뢰할 수 있는 지표다.
    ground_truth_accuracy: float | None = None


class OcrCompareService:
    def __init__(
        self,
        paddle_extractor: OcrExtractor,
        tesseract_extractor: TesseractExtractor,
        easyocr_extractor: EasyOcrExtractor,
    ) -> None:
        self._paddle_extractor = paddle_extractor
        self._tesseract_extractor = tesseract_extractor
        self._easyocr_extractor = easyocr_extractor

    def compare(
        self,
        image: Image.Image,
        reference_text: str | None = None,
    ) -> dict[str, OcrRunResult]:
        return {
            "paddle": self._run("paddle", self._paddle_extractor, image, reference_text),
            "tesseract": self._run(
                "tesseract", self._tesseract_extractor, image, reference_text
            ),
            "easyocr": self._run(
                "easyocr", self._easyocr_extractor, image, reference_text
            ),
        }

    @staticmethod
    def _run(
        engine: str,
        extractor,
        image: Image.Image,
        reference_text: str | None,
    ) -> OcrRunResult:
        start = time.perf_counter()
        elements: list[LayoutElement] = extractor.extract(image)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        elements = sorted(elements, key=lambda element: (element.y, element.x))
        text = "\n".join(element.content for element in elements)

        confidences = [
            element.confidence for element in elements if element.confidence is not None
        ]
        avg_confidence = (
            sum(confidences) / len(confidences) * 100 if confidences else None
        )

        ground_truth_accuracy = (
            compute_accuracy(reference_text, text) if reference_text else None
        )

        return OcrRunResult(
            engine=engine,
            text=text,
            char_count=len(text),
            avg_confidence=avg_confidence,
            elapsed_ms=elapsed_ms,
            ground_truth_accuracy=ground_truth_accuracy,
        )
