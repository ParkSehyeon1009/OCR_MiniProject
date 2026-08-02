import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

from app.extractors.layout import LayoutElement
from app.extractors.protocol import ExtractResult, TextExtractor
from app.models.enums import ExtractMethod


class OcrExtractor:
    def __init__(self):
        self.ocr = PaddleOCR(
            lang="korean",
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
        )

    def extract(
        self,
        image: Image.Image,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> list[LayoutElement]:

        result = self.ocr.ocr(np.array(image))

        elements: list[LayoutElement] = []

        if not result:
            return elements

        page = result[0]

        texts = page["rec_texts"]
        scores = page["rec_scores"]
        boxes = page["rec_boxes"]

        for text, score, box in zip(texts, scores, boxes):

            text = text.strip()

            if not text:
                continue

            if len(box.shape) == 1:
                # rec_boxes: [x1, y1, x2, y2]
                x = float(box[0]) + offset_x
                y = float(box[1]) + offset_y
            else:
                # rec_polys: [[x,y], ...]
                x = float(box[:, 0].min()) + offset_x
                y = float(box[:, 1].min()) + offset_y

            elements.append(
                LayoutElement(
                    x=x,
                    y=y,
                    content=text,
                    source="ocr",
                    confidence=float(score),
                )
            )

        return elements


class ImageExtractor(TextExtractor):
    # 텍스트 레이어가 없는 단일 이미지 파일(png/jpg/jpeg) 전용 추출기.
    # 좌표 계산 등 실제 OCR 로직은 OcrExtractor를 그대로 재사용한다.
    def __init__(self) -> None:
        self._ocr = OcrExtractor()

    def extract(self, file_path: str) -> ExtractResult:
        image = Image.open(file_path).convert("RGB")
        elements = self._ocr.extract(image)
        elements.sort(key=lambda e: (e.y, e.x))

        content = "\n".join(element.content for element in elements)

        return ExtractResult(
            content=content,
            page_count=1,
            char_count=len(content),
            extract_method=ExtractMethod.OCR.value,
        )