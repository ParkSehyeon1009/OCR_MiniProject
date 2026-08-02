import fitz
from PIL import Image

from app.core.config import settings
from app.extractors.layout import LayoutElement
from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.protocol import ExtractResult, TextExtractor
from app.models.enums import ExtractMethod


class PdfExtractor(TextExtractor):
    def __init__(self, ocr: OcrExtractor) -> None:
        self._ocr = ocr

    def extract(self, file_path: str) -> ExtractResult:
        page_contents: list[str] = []
        used_ocr = False

        with fitz.open(file_path) as doc:
            for page in doc:
                elements = self._extract_text_elements(page)
                text_char_count = sum(len(element.content) for element in elements)

                if text_char_count < settings.OCR_CHAR_THRESHOLD:
                    elements = self._extract_page_with_ocr(page)
                    used_ocr = True

                elements.sort(key=lambda element: (element.y, element.x))
                page_contents.append(
                    "\n".join(element.content for element in elements)
                )

            page_count = len(doc)

        content = "\n\n".join(page_contents)

        return ExtractResult(
            content=content,
            page_count=page_count,
            char_count=len(content),
            extract_method=(
                ExtractMethod.OCR.value
                if used_ocr
                else ExtractMethod.TEXT_LAYER.value
            ),
        )

    @staticmethod
    def _extract_text_elements(page: fitz.Page) -> list[LayoutElement]:
        elements: list[LayoutElement] = []

        for block in page.get_text("blocks"):
            text = str(block[4]).strip()
            if not text:
                continue

            elements.append(
                LayoutElement(
                    x=float(block[0]),
                    y=float(block[1]),
                    content=text,
                    source="text",
                )
            )

        return elements

    def _extract_page_with_ocr(self, page: fitz.Page) -> list[LayoutElement]:
        # 2배 크기로 렌더링해 작은 글자의 OCR 정확도를 높인다.
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )
        return self._ocr.extract(image)
