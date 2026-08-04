# =============================================================================
# 이 파일의 책임: OCR 비교 화면(ocr_compare_router)에 업로드된 파일을 OCR
#   엔진이 바로 돌릴 수 있는 PIL 이미지 한 장으로 변환한다.
#   - 이미지 파일(png/jpg/...)은 그대로 연다.
#   - PDF는 첫 페이지를 렌더링한다.
#   - DOCX/HWPX는 문서 안에 들어있는 첫 번째 그림을 꺼내 쓴다.
#   OCR은 원래 "이미지 안의 글자를 인식"하는 기술이라, 문서 본문의 텍스트
#   레이어(이미 글자로 저장된 부분)는 비교 대상이 아니다.
# 다른 파일과의 관계: extractors/pdf_extractor.py, docx_extractor.py,
#   hwpx_extractor.py 가 이미 하는 "문서 안 이미지 찾기"와 같은 방식을 쓰되,
#   여기서는 그 이미지를 OCR 결과로 바꾸지 않고 그대로 반환한다.
# =============================================================================

import io
import posixpath
import zipfile
from urllib.parse import unquote
from xml.etree import ElementTree as ET

import fitz
from docx import Document
from PIL import Image, UnidentifiedImageError

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".hwpx"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

_PDF_RENDER_SCALE = 2.0


def load_comparison_image(extension: str, content: bytes) -> Image.Image:
    if extension in IMAGE_EXTENSIONS:
        return _open_image(content)
    if extension == ".pdf":
        return _render_pdf_first_page(content)
    if extension == ".docx":
        return _extract_first_docx_image(content)
    if extension == ".hwpx":
        return _extract_first_hwpx_image(content)

    raise BusinessError(ErrorCode.INVALID_FILE_TYPE, detail="지원하지 않는 파일 형식입니다.")


def _open_image(content: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
        return image
    except (UnidentifiedImageError, OSError) as exc:
        raise BusinessError(ErrorCode.EXTRACTION_FAILED, detail="이미지를 열 수 없습니다.") from exc


def _render_pdf_first_page(content: bytes) -> Image.Image:
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            if document.page_count == 0:
                raise BusinessError(ErrorCode.EXTRACTION_FAILED, detail="PDF에 페이지가 없습니다.")

            pixmap = document[0].get_pixmap(
                matrix=fitz.Matrix(_PDF_RENDER_SCALE, _PDF_RENDER_SCALE),
                alpha=False,
            )
            return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    except BusinessError:
        raise
    except Exception as exc:
        raise BusinessError(ErrorCode.EXTRACTION_FAILED, detail="PDF를 열 수 없습니다.") from exc


def _extract_first_docx_image(content: bytes) -> Image.Image:
    try:
        doc = Document(io.BytesIO(content))
    except Exception as exc:
        raise BusinessError(
            ErrorCode.EXTRACTION_FAILED, detail="DOCX 파일을 열 수 없습니다."
        ) from exc

    for rel in doc.part.rels.values():
        if "image" not in rel.reltype:
            continue
        try:
            return _open_image(rel.target_part.blob)
        except BusinessError:
            # 이 이미지만 해석 실패 — 다음 이미지를 계속 찾아본다.
            continue

    raise BusinessError(
        ErrorCode.EXTRACTION_FAILED,
        detail="DOCX 안에서 OCR로 비교할 이미지를 찾지 못했습니다.",
    )


def _extract_first_hwpx_image(content: bytes) -> Image.Image:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            manifest_name = "Contents/content.hpf"
            if manifest_name not in archive.namelist():
                raise BusinessError(
                    ErrorCode.EXTRACTION_FAILED, detail="HWPX 매니페스트를 찾을 수 없습니다."
                )

            root = ET.fromstring(archive.read(manifest_name))

            for element in root.iter():
                if element.tag.rsplit("}", 1)[-1] != "item":
                    continue

                href = element.get("href")
                media_type = element.get("media-type", "")
                if not href or not media_type.startswith("image/"):
                    continue

                normalized_path = posixpath.normpath(unquote(href)).lstrip("/")

                # ZIP 밖을 가리키는 상대 경로는 허용하지 않는다.
                if normalized_path == ".." or normalized_path.startswith("../"):
                    continue
                if normalized_path not in archive.namelist():
                    continue

                try:
                    return _open_image(archive.read(normalized_path))
                except BusinessError:
                    continue
    except BusinessError:
        raise
    except Exception as exc:
        raise BusinessError(
            ErrorCode.EXTRACTION_FAILED, detail="HWPX 파일을 열 수 없습니다."
        ) from exc

    raise BusinessError(
        ErrorCode.EXTRACTION_FAILED,
        detail="HWPX 안에서 OCR로 비교할 이미지를 찾지 못했습니다.",
    )
