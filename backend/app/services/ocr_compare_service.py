import time
from dataclasses import dataclass

from PIL import Image

from app.extractors.easyocr_extractor import EasyOcrExtractor
from app.extractors.layout import LayoutElement
from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.tesseract_extractor import TesseractExtractor


@dataclass(frozen=True)
class OcrRunResult:
    engine: str
    text: str
    char_count: int
    # 정답 텍스트가 없어 실제 정확도를 계산할 수 없으므로, 각 엔진이 자체적으로
    # 보고하는 인식 신뢰도(confidence) 평균을 "정확도" 대용으로 사용한다 (0~100%).
    avg_confidence: float | None
    elapsed_ms: int


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

    def compare(self, image: Image.Image) -> dict[str, OcrRunResult]:
        return {
            "paddle": self._run("paddle", self._paddle_extractor, image),
            "tesseract": self._run("tesseract", self._tesseract_extractor, image),
            "easyocr": self._run("easyocr", self._easyocr_extractor, image),
        }

    @staticmethod
    def _run(engine: str, extractor, image: Image.Image) -> OcrRunResult:
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

        return OcrRunResult(
            engine=engine,
            text=text,
            char_count=len(text),
            avg_confidence=avg_confidence,
            elapsed_ms=elapsed_ms,
        )
