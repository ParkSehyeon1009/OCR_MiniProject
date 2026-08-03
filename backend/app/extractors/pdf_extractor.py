from io import BytesIO
from typing import Any

import fitz
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError
from app.extractors.layout import LayoutElement
from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.protocol import ExtractResult, TextExtractor
from app.models.enums import ExtractMethod


class PdfExtractor(TextExtractor):
    def __init__(self, ocr: OcrExtractor) -> None:
        self._ocr = ocr

    def extract(self, file_path: str) -> ExtractResult:
        page_contents: list[str] = []

        has_text = False
        has_ocr = False

        with fitz.open(file_path) as document:
            page_count = len(document)

            if page_count > settings.MAX_PAGES:
                raise BusinessError(
                    ErrorCode.TOO_MANY_PAGES,
                    detail=f"PDF는 최대 {settings.MAX_PAGES}페이지까지 업로드할 수 있습니다.",
                )

            for page in document:
                elements, page_has_text, page_has_ocr = self._extract_page(page)

                has_text = has_text or page_has_text
                has_ocr = has_ocr or page_has_ocr

                elements.sort(key=lambda element: (element.y, element.x))

                page_content = "\n".join(
                    element.content
                    for element in elements
                    if element.content.strip()
                )

                page_contents.append(page_content)

        content = "\n\n".join(page_contents)

        if has_text and has_ocr:
            extract_method = ExtractMethod.HYBRID.value
        elif has_ocr:
            extract_method = ExtractMethod.OCR.value
        else:
            extract_method = ExtractMethod.TEXT_LAYER.value

        return ExtractResult(
            content=content,
            page_count=page_count,
            char_count=len(content),
            extract_method=extract_method,
        )

    def _extract_page(
        self,
        page: fitz.Page,
    ) -> tuple[list[LayoutElement], bool, bool]:
        page_dict: dict[str, Any] = page.get_text("dict")

        elements: list[LayoutElement] = []
        has_text = False
        has_ocr = False

        for block in page_dict.get("blocks", []):
            block_type = block.get("type")

            if block_type == 0:
                text_element = self._extract_text_block(block)

                if text_element is not None:
                    elements.append(text_element)
                    has_text = True

            elif block_type == 1:
                image_elements = self._extract_image_block(block)

                if image_elements:
                    elements.extend(image_elements)
                    has_ocr = True

        # 텍스트와 이미지 OCR 결과가 모두 없으면 페이지 전체를 OCR한다.
        if not elements:
            page_ocr_elements = self._extract_full_page_with_ocr(page)

            if page_ocr_elements:
                elements.extend(page_ocr_elements)
                has_ocr = True

        return elements, has_text, has_ocr

    @staticmethod
    def _extract_text_block(
        block: dict[str, Any],
    ) -> LayoutElement | None:
        lines: list[str] = []

        for line in block.get("lines", []):
            spans: list[str] = []

            for span in line.get("spans", []):
                text = str(span.get("text", "")).strip()

                if text:
                    spans.append(text)

            line_text = " ".join(spans).strip()

            if line_text:
                lines.append(line_text)

        content = "\n".join(lines).strip()

        if not content:
            return None

        bbox = block.get("bbox", (0, 0, 0, 0))

        return LayoutElement(
            x=float(bbox[0]),
            y=float(bbox[1]),
            content=content,
            source="text",
        )

    def _extract_image_block(
        self,
        block: dict[str, Any],
    ) -> list[LayoutElement]:
        image_bytes = block.get("image")
        bbox = block.get("bbox", (0, 0, 0, 0))

        if not image_bytes:
            return []

        try:
            with Image.open(BytesIO(image_bytes)) as source_image:
                image = source_image.convert("RGB")

                image_width = image.width
                image_height = image.height

                if image_width <= 0 or image_height <= 0:
                    return []

                ocr_elements = self._ocr.extract(image)

        except (UnidentifiedImageError, OSError, ValueError):
            return []

        if not ocr_elements:
            return []

        x0 = float(bbox[0])
        y0 = float(bbox[1])
        x1 = float(bbox[2])
        y1 = float(bbox[3])

        displayed_width = max(x1 - x0, 1.0)
        displayed_height = max(y1 - y0, 1.0)

        scale_x = displayed_width / image_width
        scale_y = displayed_height / image_height

        converted_elements: list[LayoutElement] = []

        for element in ocr_elements:
            # OCR 결과의 이미지 픽셀 좌표를 PDF 페이지 좌표로 변환한다.
            # 이 변환을 해야 텍스트 블록과 이미지 내부 글자를 같은 기준으로
            # 정렬할 수 있다.
            converted_elements.append(
                LayoutElement(
                    x=x0 + element.x * scale_x,
                    y=y0 + element.y * scale_y,
                    content=element.content,
                    source="ocr",
                    confidence=element.confidence,
                )
            )

        return converted_elements

    def _extract_full_page_with_ocr(
        self,
        page: fitz.Page,
    ) -> list[LayoutElement]:
        # 2배 크기로 렌더링해 작은 글자의 OCR 정확도를 높인다.
        scale = 2.0
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            alpha=False,
        )

        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )

        ocr_elements = self._ocr.extract(image)

        converted_elements: list[LayoutElement] = []

        for element in ocr_elements:
            # 2배로 렌더링한 이미지의 좌표를 원래 PDF 페이지 좌표로 복원한다.
            converted_elements.append(
                LayoutElement(
                    x=element.x / scale,
                    y=element.y / scale,
                    content=element.content,
                    source="ocr",
                    confidence=element.confidence,
                )
            )

        return converted_elements