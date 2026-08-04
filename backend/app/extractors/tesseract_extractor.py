from PIL import Image
from pytesseract import Output, image_to_data

from app.extractors.layout import LayoutElement

# confidence는 PaddleOCR(rec_scores, 0~1)과 스케일을 맞추기 위해 0~1로 정규화한다.
_TESSERACT_CONFIDENCE_SCALE = 100


class TesseractExtractor:
    def extract(self, image: Image.Image) -> list[LayoutElement]:
        rgb_image = image.convert("RGB")
        data = image_to_data(rgb_image, lang="kor+eng", output_type=Output.DICT)

        elements: list[LayoutElement] = []
        word_count = len(data["text"])

        for i in range(word_count):
            text = data["text"][i].strip()
            if not text:
                continue

            # 텍스트가 아닌 영역(줄/블록 등)은 conf가 -1로 내려온다.
            try:
                confidence = float(data["conf"][i])
            except (TypeError, ValueError):
                continue
            if confidence < 0:
                continue

            elements.append(
                LayoutElement(
                    x=float(data["left"][i]),
                    y=float(data["top"][i]),
                    content=text,
                    source="ocr",
                    confidence=confidence / _TESSERACT_CONFIDENCE_SCALE,
                )
            )

        return elements
