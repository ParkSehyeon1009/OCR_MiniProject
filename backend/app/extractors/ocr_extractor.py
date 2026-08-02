from threading import Lock

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image

from app.extractors.layout import LayoutElement


class OcrExtractor:
    def __init__(self) -> None:
        self._ocr = PaddleOCR(
            lang="korean",
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
        )

        # 여러 요청이 같은 OCR 모델을 동시에 사용하지 못하도록 제어한다.
        self._inference_lock = Lock()

    def extract(
        self,
        image: Image.Image,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> list[LayoutElement]:
        rgb_image = image.convert("RGB")

        # 동시에 여러 요청이 들어와도 OCR은 한 번에 하나씩 실행한다.
        with self._inference_lock:
            results = self._ocr.ocr(np.asarray(rgb_image))

        if not results:
            return []

        page = results[0]

        if page is None:
            return []

        texts = page.get("rec_texts", [])
        scores = page.get("rec_scores", [])

        boxes = page.get("rec_boxes")

        # rec_boxes가 없으면 다각형 좌표인 rec_polys를 사용한다.
        if boxes is None or len(boxes) == 0:
            boxes = page.get("rec_polys", [])

        elements: list[LayoutElement] = []

        for text, score, box in zip(texts, scores, boxes):
            normalized_text = str(text).strip()

            if not normalized_text:
                continue

            box_array = np.asarray(box)

            if box_array.ndim == 1:
                # rec_boxes 형식: [x1, y1, x2, y2]
                x = float(box_array[0])
                y = float(box_array[1])
            else:
                # rec_polys 형식: [[x1, y1], [x2, y2], ...]
                x = float(box_array[:, 0].min())
                y = float(box_array[:, 1].min())

            elements.append(
                LayoutElement(
                    x=x + offset_x,
                    y=y + offset_y,
                    content=normalized_text,
                    source="ocr",
                    confidence=float(score),
                )
            )

        return elements
