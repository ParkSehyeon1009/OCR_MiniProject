import docx
from docx.oxml.ns import qn

from app.extractors.protocol import ExtractResult, TextExtractor
from app.models.enums import ExtractMethod


class DocxExtractor(TextExtractor):
    def extract(self, file_path: str) -> ExtractResult:
        document = docx.Document(file_path)

        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text)

        content = "\n".join(paragraphs)

        return ExtractResult(
            content=content,
            page_count=self._count_pages(document),
            char_count=len(content),
            extract_method=ExtractMethod.DOCX.value,
        )

    @staticmethod
    def _count_pages(document: docx.document.Document) -> int:
        # python-docx는 렌더링 페이지 수를 제공하지 않으므로, 저자가 넣은
        # 명시적 페이지 나눔(w:br type="page") 개수 + 1로 근사한다.
        page_breaks = sum(
            1
            for br in document.element.body.iter(qn("w:br"))
            if br.get(qn("w:type")) == "page"
        )
        return page_breaks + 1
