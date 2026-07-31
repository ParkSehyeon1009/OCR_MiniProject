import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

from app.extractors.layout import LayoutElement


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