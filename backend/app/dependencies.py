# =============================================================================
# 이 파일의 책임: FastAPI Depends()로 주입할 객체들을 한 곳에서 조립한다.
#   (1) AI 클라이언트: settings.USE_FAKE_AI에 따라 FakeAIClient/OpenAIClient 선택.
#   (2) Repository: Depends(get_db)로 받은 세션을 감싸 생성.
#   (3) Extractor/Analyzer 레지스트리: 확장자/분석기 타입 -> 구현체 매핑.
#   담당자 A/B/C가 pdf/docx/hwpx/ocr extractor, summary/category analyzer를
#   완성하면, 아래 TODO 표시된 자리에 register()만 추가하면 된다 (§2-3).
# 다른 파일과의 관계: api/routes/*.py(라우터, 담당자 A/B/C가 구현)가 이 모듈의
#   함수들을 Depends(...)로 가져다 쓴다. services/*.py 생성자에도 이 함수들의
#   반환값이 주입된다.
# Spring 비교: Spring의 @Configuration + @Bean 메서드 모음과 같은 위치.
#   Spring은 @Profile("fake")/@ConditionalOnProperty로 구현체를 스위칭하지만,
#   여기서는 settings.USE_FAKE_AI 값을 보고 if/else로 직접 선택한다.
# =============================================================================

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.client_protocol import AIClientProtocol
from app.ai.fake_client import FakeAIClient
from app.ai.openai_client import OpenAIClient
from app.analyzers.protocol import Analyzer
from app.core.config import settings
from app.db.session import get_db
from app.extractors.fake_extractor import FakeExtractor
from app.extractors.registry import ExtractorRegistry
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.document_repository import DocumentRepository


@lru_cache
def get_ai_client() -> AIClientProtocol:
    # USE_FAKE_AI 기본값은 True — 개발 중 실수로 실제 API가 호출되어 비용이
    # 발생하는 것을 막기 위한 안전장치다. 실제 호출은 .env에서 명시적으로
    # USE_FAKE_AI=false로 바꿔야만 일어난다.
    if settings.USE_FAKE_AI:
        return FakeAIClient()
    return OpenAIClient(settings)


@lru_cache
def get_extractor_registry() -> ExtractorRegistry:
    registry = ExtractorRegistry()
    # TODO: 담당자 A가 pdf/docx/hwpx/ocr extractor를 구현한 뒤 아래처럼 등록하세요.
    #   registry.register("pdf", PdfExtractor())
    #   registry.register("docx", DocxExtractor())
    #   registry.register("hwpx", HwpxExtractor())
    #   registry.register("png", OcrExtractor())
    #   registry.register("jpg", OcrExtractor())
    #   registry.register("jpeg", OcrExtractor())
    # 지금은 참고/개발용으로 FakeExtractor만 등록해둔다.
    registry.register("fake", FakeExtractor())
    return registry


@lru_cache
def get_analyzer_registry() -> dict[str, Analyzer]:
    # TODO: 담당자 B가 summary_analyzer.py / category_analyzer.py를 구현한 뒤
    #   analyzer_type 문자열을 key로 등록하세요.
    #   registry["summary"] = SummaryAnalyzer(get_ai_client())
    #   registry["category"] = CategoryAnalyzer(get_ai_client())
    registry: dict[str, Analyzer] = {}
    return registry


def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


def get_analysis_repository(db: Session = Depends(get_db)) -> AnalysisRepository:
    return AnalysisRepository(db)
