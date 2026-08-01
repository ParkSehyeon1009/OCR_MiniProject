from sqlalchemy.orm import Session

from app.analyzers.protocol import Analyzer, AnalyzeResult
from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError
from app.core.transaction import transactional
from app.models.document import Analysis
from app.models.enums import AnalyzerType
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.document_repository import DocumentRepository

DEFAULT_ANALYZER_TYPES = [AnalyzerType.SUMMARY.value, AnalyzerType.CATEGORY.value]


class AnalysisService:
    def __init__(
        self,
        db: Session,
        document_repository: DocumentRepository,
        analysis_repository: AnalysisRepository,
        analyzer_registry: dict[str, Analyzer],
    ) -> None:
        self._db = db
        self._document_repository = document_repository
        self._analysis_repository = analysis_repository
        self._analyzer_registry = analyzer_registry

    async def analyze_document(
        self, document_id: int, analyzer_types: list[str] | None
    ) -> list[Analysis]:
        document = self._document_repository.get_by_id(document_id)
        if document is None:
            raise BusinessError(ErrorCode.DOCUMENT_NOT_FOUND)
        if document.extracted_text is None:
            raise BusinessError(ErrorCode.NOT_EXTRACTED_YET)

        types = analyzer_types or DEFAULT_ANALYZER_TYPES

        # AI를 호출하기 전에 모든 analyzer_type이 등록돼 있는지 먼저 검증한다.
        # (뒤쪽 타입이 잘못된 경우, 앞쪽 analyzer의 AI 호출 비용까지 낭비한 뒤
        #  에러를 내는 것을 피하기 위함)
        analyzers: list[tuple[str, Analyzer]] = []
        for analyzer_type in types:
            analyzer = self._analyzer_registry.get(analyzer_type)
            if analyzer is None:
                raise BusinessError(ErrorCode.ANALYZER_NOT_FOUND)
            analyzers.append((analyzer_type, analyzer))

        content = document.extracted_text.content
        results: list[tuple[str, AnalyzeResult]] = []
        for analyzer_type, analyzer in analyzers:
            result = await analyzer.analyze(content)
            results.append((analyzer_type, result))

        # DB 커밋은 AI 호출이 모두 끝난 뒤 한 트랜잭션으로 묶는다 — AI 응답을
        # 기다리는 동안 DB 트랜잭션을 열어두지 않기 위함.
        with transactional(self._db):
            analyses = [
                self._analysis_repository.create(
                    Analysis(
                        document_id=document.id,
                        analyzer_type=analyzer_type,
                        result_json=result.result,
                        provider=result.provider,
                        model_name=result.model_name,
                        prompt_version=result.prompt_version,
                        tokens_in=result.tokens_in,
                        tokens_out=result.tokens_out,
                        latency_ms=result.latency_ms,
                    )
                )
                for analyzer_type, result in results
            ]

        return analyses
