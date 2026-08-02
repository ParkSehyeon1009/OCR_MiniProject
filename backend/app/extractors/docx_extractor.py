from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.document import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

from io import BytesIO
from PIL import Image

from app.extractors.ocr_extractor import OcrExtractor
from app.extractors.protocol import ExtractResult, TextExtractor


class DocxExtractor(TextExtractor):
    def __init__(self):
        self.ocr = OcrExtractor()

    def extract(self, file_path: str) -> ExtractResult:
        doc = Document(file_path)

        contents: list[str] = []

        for block in self._iter_block_items(doc):

                if isinstance(block, Paragraph):
                    self._extract_paragraph(block, contents)

                elif isinstance(block, Table):
                    self._extract_table(block, contents)

        content = "\n".join(contents)

        return ExtractResult(
            content=content,
            page_count=1,
            char_count=len(content),
            extract_method="docx",
        )

    def _iter_block_items(self, doc: DocxDocument):

        parent = doc.element.body

        for child in parent.iterchildren():

            if isinstance(child, CT_P):
                yield Paragraph(child, doc)

            elif isinstance(child, CT_Tbl):
                yield Table(child, doc)

    def _extract_paragraph(
        self,
        paragraph: Paragraph,
        contents: list[str],
    ):

        text = paragraph.text.strip()

        if text:
            contents.append(text)

        self._extract_images(paragraph, contents)

    def _extract_table(
        self,
        table: Table,
        contents: list[str],
    ):

        for row in table.rows:

            row_contents: list[str] = []

            for cell in row.cells:

                cell_text = []

                # 셀 안 문단 순회
                for paragraph in cell.paragraphs:

                    text = paragraph.text.strip()

                    if text:
                        cell_text.append(text)

                    # 셀 안 이미지 OCR
                    self._extract_images(paragraph, cell_text)

                if cell_text:
                    row_contents.append("\n".join(cell_text))

            if row_contents:
                contents.append(" | ".join(row_contents))

    def _extract_images(
        self,
        paragraph: Paragraph,
        contents: list[str],
    ):
        """
        문단 내부 이미지 OCR
        """

        # paragraph 안의 drawing 태그 찾기
        drawings = paragraph._element.xpath(".//w:drawing")

        for drawing in drawings:

            # drawing 안의 이미지(blip) 찾기
            blips = drawing.xpath(".//a:blip")

            for blip in blips:

                embed = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )

                if embed is None:
                    continue

                try:
                    image_part = paragraph.part.related_parts[embed]

                except KeyError:
                    continue

                text = self._ocr_image(image_part.blob)

                if text:
                    contents.append(text)

    def _ocr_image(self, image_bytes: bytes) -> str:
        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")

            elements = self.ocr.extract(image)

            return "\n".join(
                element.content
                for element in elements
                if element.content.strip()
            )
        except Exception:
            return ""