import fitz
from PIL import Image

from app.extractors.layout import LayoutElement
from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.protocol import ExtractResult, TextExtractor


class PdfExtractor(TextExtractor):
    def __init__(self):
        self.ocr = OcrExtractor()

    def extract(self, file_path: str) -> ExtractResult:
        doc = fitz.open(file_path)

        elements: list[LayoutElement] = []

        try:
            for page in doc:
                # =====================
                # 1. PDF 텍스트 추출
                # =====================
                blocks = page.get_text("blocks")

                for block in blocks:
                    x0 = float(block[0])
                    y0 = float(block[1])
                    text = block[4].strip()

                    if not text:
                        continue

                    elements.append(
                        LayoutElement(
                            x=x0,
                            y=y0,
                            content=text,
                            source="text",
                            confidence=None,
                        )
                    )

                # =====================
                # 2. PDF 이미지 추출
                # =====================
                image_infos = page.get_image_info(xrefs=True)

                for image_info in image_infos:
                    xref = image_info["xref"]

                    rects = page.get_image_rects(xref)

                    if not rects:
                        continue

                    rect = rects[0]

                    pix = fitz.Pixmap(doc, xref)

                    try:
                        if pix.n > 3:
                            rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                        else:
                            rgb_pix = pix

                        image = Image.frombytes(
                            "RGB",
                            (rgb_pix.width, rgb_pix.height),
                            rgb_pix.samples,
                        )

                        ocr_elements = self.ocr.extract(
                            image=image,
                            offset_x=rect.x0,
                            offset_y=rect.y0,
                        )

                        elements.extend(ocr_elements)

                    finally:
                        pix = None
                        rgb_pix = None

            # =====================
            # 3. 좌표 기준 정렬
            # =====================
            elements.sort(key=lambda e: (e.y, e.x))

            content = "\n".join(
                element.content
                for element in elements
            )

            return ExtractResult(
                content=content,
                page_count=len(doc),
                char_count=len(content),
                extract_method="PDF",
            )

        finally:
            doc.close()