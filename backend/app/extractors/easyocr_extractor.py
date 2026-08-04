from threading import Lock

import easyocr
import numpy as np
from PIL import Image

from app.extractors.layout import LayoutElement


class EasyOcrExtractor:
    def __init__(self) -> None:
        self._reader = easyocr.Reader(["ko", "en"], gpu=False)

        # PaddleOCR과 마찬가지로 모델 인퍼런스를 동시에 여러 요청이 타지 않게 막는다.
        self._inference_lock = Lock()

    def extract(self, image: Image.Image) -> list[LayoutElement]:
        rgb_image = image.convert("RGB")

        with self._inference_lock:
            # readtext()는 (사각형 4개 꼭짓점, 텍스트, confidence) 튜플의 리스트를 반환한다.
            results = self._reader.readtext(np.asarray(rgb_image))

        elements: list[LayoutElement] = []

        for box, text, confidence in results:
            normalized_text = str(text).strip()
            if not normalized_text:
                continue

            xs = [point[0] for point in box]
            ys = [point[1] for point in box]

            elements.append(
                LayoutElement(
                    x=float(min(xs)),
                    y=float(min(ys)),
                    content=normalized_text,
                    source="ocr",
                    confidence=float(confidence),
                )
            )

        return elements
