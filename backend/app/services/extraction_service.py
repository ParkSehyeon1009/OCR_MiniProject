import os
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError
from app.core.transaction import transactional
from app.extractors.registry import ExtractorRegistry
from app.models.document import Document, ExtractedText
from app.models.enums import DocumentStatus
from app.repositories.document_repository import DocumentRepository

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".hwpx", ".png", ".jpg", ".jpeg"}


class ExtractionService:
    def __init__(
        self,
        db: Session,
        document_repository: DocumentRepository,
        extractor_registry: ExtractorRegistry,
    ) -> None:
        self._db = db
        self._document_repository = document_repository
        self._extractor_registry = extractor_registry

    def upload_and_extract(self, filename: str, content: bytes) -> Document:
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise BusinessError(ErrorCode.INVALID_FILE_TYPE, detail=f"file_type={extension}")

        if len(content) > settings.max_file_size_bytes:
            raise BusinessError(
                ErrorCode.FILE_TOO_LARGE,
                detail=f"size={len(content)}bytes, max={settings.max_file_size_bytes}bytes",
            )

        stored_path = self._save_file(filename, content)

        try:
            file_type = extension.lstrip(".")
            extractor = self._extractor_registry.get(file_type)

            try:
                result = extractor.extract(stored_path)
            except BusinessError:
                raise
            except Exception as exc:
                raise BusinessError(ErrorCode.EXTRACTION_FAILED) from exc

            if result.page_count > settings.MAX_PAGES:
                raise BusinessError(
                    ErrorCode.TOO_MANY_PAGES,
                    detail=f"page_count={result.page_count}, max={settings.MAX_PAGES}",
                )

            with transactional(self._db):
                document = self._document_repository.create(
                    Document(
                        filename=filename,
                        stored_path=stored_path,
                        file_type=file_type,
                        file_size=len(content),
                        status=DocumentStatus.EXTRACTED.value,
                    )
                )
                document.extracted_text = ExtractedText(
                    content=result.content,
                    page_count=result.page_count,
                    char_count=result.char_count,
                    extract_method=result.extract_method,
                )

            return document
        except Exception:
            # 검증/추출/DB 저장 중 어느 단계에서 실패하든, 이미 디스크에 쓴
            # 원본 파일이 고아 파일로 남지 않도록 정리한다.
            if os.path.exists(stored_path):
                os.remove(stored_path)
            raise

    def _save_file(self, filename: str, content: bytes) -> str:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        stored_path = os.path.join(settings.UPLOAD_DIR, unique_name)
        with open(stored_path, "wb") as f:
            f.write(content)
        return stored_path
