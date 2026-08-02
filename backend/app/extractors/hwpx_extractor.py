import re
import zipfile
from xml.etree import ElementTree as ET

from app.extractors.protocol import ExtractResult, TextExtractor
from app.models.enums import ExtractMethod

_SECTION_PATTERN = re.compile(r"Contents/section\d+\.xml")


class HwpxExtractor(TextExtractor):
    def extract(self, file_path: str) -> ExtractResult:
        with zipfile.ZipFile(file_path) as archive:
            section_names = sorted(
                name for name in archive.namelist() if _SECTION_PATTERN.fullmatch(name)
            )

            texts: list[str] = []
            for name in section_names:
                root = ET.fromstring(archive.read(name))
                # HWPX(OWPML) 버전마다 네임스페이스 URI가 달라질 수 있어,
                # 태그의 local-name만으로 텍스트 런("t") 요소를 찾는다.
                for element in root.iter():
                    local_name = element.tag.rsplit("}", 1)[-1]
                    if local_name == "t" and element.text:
                        texts.append(element.text)

        content = "\n".join(texts)

        return ExtractResult(
            content=content,
            page_count=max(len(section_names), 1),
            char_count=len(content),
            extract_method=ExtractMethod.HWPX.value,
        )
