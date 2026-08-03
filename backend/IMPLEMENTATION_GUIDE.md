# PDF Brief AI — 담당자별 구현 가이드

공통 인프라(`db/`, `models/`, `schemas/`, `repositories/`, `dependencies.py`, `extractors/protocol.py`,
`analyzers/protocol.py`, `ai/*`)는 이미 만들어져 있습니다. 아래 내용은 각자 담당 영역을
직접 설계·구현할 때 참고할 자료입니다. **머지 충돌을 피하기 위해 담당자별로 파일을 분리했으니,
다른 담당자의 라우터/서비스 파일은 건드리지 마세요.**

---

## 공통 규칙

- Router → Service → Repository/Client 순서로만 의존합니다. Router에 비즈니스 로직을 넣지 마세요.
  Service에서 DB 세션을 직접 다루지 말고 Repository를 거치세요.
- API 필드명은 전부 snake_case입니다 (camelCase 변환 금지).
- 새 라우터 파일은 `APIRouter(prefix="/api", tags=[...])`로 만들고, `app/main.py`의
  주석 처리된 import/`include_router` 두 줄을 자신의 담당 라우터만 해제하세요.
- 여러 Repository 호출을 한 트랜잭션으로 묶어야 하면 `app/core/transaction.py`의
  `transactional(db)` 컨텍스트매니저를 사용하세요.
- AI 클라이언트가 필요하면 `app/dependencies.py`의 `get_ai_client()`를 사용하세요.
  `.env`의 `USE_FAKE_AI=true`(기본값)일 때는 실제 API가 호출되지 않습니다.

---

## 담당자 A — 업로드 + 텍스트 추출

**만들 파일**
- `app/extractors/pdf_extractor.py`
- `app/extractors/docx_extractor.py`
- `app/extractors/hwpx_extractor.py`
- `app/extractors/ocr_extractor.py`
- `app/services/extraction_service.py`
- `app/api/routes/upload_router.py`

**구현할 Protocol** — `app/extractors/protocol.py`
- `TextExtractor.extract(self, file_path: str) -> ExtractResult` (동기 메서드, async 아님)
- `ExtractResult`: `content: str`, `page_count: int`, `char_count: int`, `extract_method: str`

**참고할 기존 파일**
- `app/extractors/fake_extractor.py` — Protocol을 만족하는 최소 구현 예시
- `app/extractors/registry.py` — 확장자별 Extractor를 등록/조회하는 레지스트리
- `app/dependencies.py`의 `get_extractor_registry()` — 여기 TODO 자리에
  `registry.register("pdf", PdfExtractor())`처럼 추가하세요

**주의할 점**
- `ocr_extractor.py`는 OCR 라이브러리(예: easyocr)를 `requirements.txt`에 아직 추가하지 않았습니다.
  다른 담당자가 아직 그 패키지를 설치하지 않은 환경에서도 앱이 뜨도록, OCR 관련 import는
  **모듈 최상단이 아니라 함수/메서드 본문 안에서** 하세요. (최상단 import면 그 패키지가 없는
  환경에서는 서버 자체가 뜨지 않습니다.)
- 업로드 라우터는 **동기(`def`)**로 작성하세요. `async def`로 만들면 안 됩니다 — 텍스트 추출은
  CPU/파일 I/O 작업이라 FastAPI의 threadpool에서 도는 동기 라우터가 더 적합합니다.
- 검증 규칙: 최대 10MB(`settings.MAX_FILE_SIZE_MB`), PDF 최대 30페이지(`settings.MAX_PAGES`),
  DOCX/HWPX 최대 추출 텍스트 45,000자(`settings.MAX_EXTRACTED_CHARS`), 허용 확장자
  `.pdf .docx .hwpx .png .jpg .jpeg`. 실패 시 `BusinessError(ErrorCode.FILE_TOO_LARGE)`,
  `BusinessError(ErrorCode.TOO_MANY_PAGES)`, `BusinessError(ErrorCode.CONTENT_TOO_LARGE)`,
  `BusinessError(ErrorCode.INVALID_FILE_TYPE)`을 사용하세요.
- 추출 실패 시 `BusinessError(ErrorCode.EXTRACTION_FAILED)`.
- 텍스트 레이어가 없는 PDF/이미지는 `settings.OCR_CHAR_THRESHOLD`보다 추출된 글자 수가 적으면
  OCR로 폴백하는 방식으로 설계하는 것을 권장합니다.
- 업로드된 원본 파일은 `settings.UPLOAD_DIR`에 저장하고 그 경로를 `documents.stored_path`에 기록하세요.

**완료 판단 기준**
- `uvicorn app.main:app --reload` 후 `/docs`에서 `POST /api/documents`에 실제 PDF 파일을
  업로드하면 201 응답과 함께 `id, filename, file_type, document_type, status, page_count,
  char_count, extract_method, created_at`이 반환된다.
- 10MB 초과 파일, 지원하지 않는 확장자 업로드 시 각각 413/400 에러 응답이 온다.

---

## 담당자 B — LLM 분석 (요약/카테고리)

**만들 파일**
- `app/analyzers/summary_analyzer.py`
- `app/analyzers/category_analyzer.py`
- `app/analyzers/prompts.py`
- `app/services/analysis_service.py`
- `app/api/routes/analysis_router.py`

**구현할 Protocol** — `app/analyzers/protocol.py`
- `Analyzer.analyze(self, text: str) -> AnalyzeResult` (async 메서드)
- `AnalyzeResult`: `result: dict`, `provider: str`, `model_name: str`, `prompt_version: str`,
  `tokens_in: int | None`, `tokens_out: int | None`, `latency_ms: int | None`
- 내부에서 `app/ai/client_protocol.py`의 `AIClientProtocol.generate_with_meta(prompt) -> AIResult`를
  호출해서 `AnalyzeResult`의 provider/model_name/tokens_in/tokens_out/latency_ms를 채우세요.

**참고할 기존 파일**
- `app/ai/fake_client.py` — `generate_with_meta`가 토큰 수/지연 시간을 어떻게 채우는지 참고
- `app/dependencies.py`의 `get_analyzer_registry()` — 여기 TODO 자리에
  `registry["summary"] = SummaryAnalyzer(get_ai_client())`처럼 추가하세요
- `app/repositories/analysis_repository.py` — analyses 저장/조회

**주의할 점**
- `POST /api/documents/{id}/analyze` 라우터만 **`async def`**로 작성하세요 (AI 호출을 `await`해야
  하므로). 이 외의 모든 라우터는 동기(`def`)로 유지합니다.
- 업로드와 별도 엔드포인트이므로, 이미 추출된 텍스트가 없으면
  `BusinessError(ErrorCode.NOT_EXTRACTED_YET)`을 던지세요.
- 요청 바디의 `analyzer_types`가 없으면 summary/category를 모두 실행하세요.
  등록되지 않은 analyzer_type이 들어오면 `BusinessError(ErrorCode.ANALYZER_NOT_FOUND)`.
- AI 호출 실패/타임아웃은 각각 `BusinessError(ErrorCode.AI_PROVIDER_ERROR)`,
  `BusinessError(ErrorCode.AI_TIMEOUT)`으로 감싸는 것을 권장합니다 (`settings.AI_TIMEOUT_SECONDS` 참고).
- `result`는 분석기마다 구조가 다른 `dict`이므로 고정 스키마를 만들지 마세요.
- 재분석 시 기존 analyses 행을 지우지 말고 새 행을 추가하세요 (1:N 유지, 모델 비교 실험용).
- 카테고리 후보 값(5~8개)은 팀 회의에서 확정합니다. 확정 전에는 임시 목록으로 개발하고,
  확정 후 prompts.py의 상수만 교체하세요.
- 카테고리 값은 Literal 타입으로 고정해 LLM이 임의의 값을 반환하지 못하게 하세요.
  값이 일관되지 않으면 담당자 C의 category 필터 기능이 동작하지 않습니다.


**완료 판단 기준**
- 업로드된 문서에 대해 `/docs`에서 `POST /api/documents/{id}/analyze`를 호출하면 200 응답과
  함께 `document_id`, `analyses[]`(각각 `analyzer_type, result, provider, model_name, tokens_in,
  tokens_out, latency_ms, created_at`)가 반환된다.
- 같은 문서를 다시 analyze 호출하면 analyses에 행이 추가된다(덮어쓰지 않음).

---

## 담당자 C — 목록/상세/검색/다운로드/삭제

**만들 파일**
- `app/services/document_service.py`
- `app/api/routes/document_router.py`

**참고할 기존 파일**
- `app/repositories/document_repository.py` — `search(q, document_type, category, page, size)`가
  이미 파일명/본문 부분검색 + document_type/category 필터 + 페이징을 구현해두었습니다.
- `app/schemas/document.py` — `DocumentListItem`, `DocumentDetailResponse`, `AnalysisResponse`
- `app/schemas/common.py` — `PageResponse[T]` (목록 응답을 이걸로 감싸세요)

**주의할 점**
- 이 4개 엔드포인트는 모두 **동기(`def`)** 라우터입니다.
- `GET /api/documents`의 `category` 필터는 analyses 테이블의 `analyzer_type == "category"`
  결과(JSONB)에서 뽑아옵니다. `summary_preview`는 summary 분석 결과 텍스트를 100자로 자른 값입니다.
  (아직 분석이 안 된 문서는 `category`/`summary_preview`를 `null`로 두세요.)
- 상세 조회(`GET /api/documents/{id}`)는 문서가 없으면 `BusinessError(ErrorCode.DOCUMENT_NOT_FOUND)`.
- 다운로드(`GET /api/documents/{id}/download?format=txt`)는 `Content-Disposition` 헤더에
  한글 파일명이 깨지지 않도록 `filename*=UTF-8''...` (URL 인코딩) 형식을 사용하세요.
  `FileResponse`/`StreamingResponse` 중 편한 쪽을 쓰되, 원본 대신 추출된 텍스트를 내려주면 됩니다.
- 삭제(`DELETE /api/documents/{id}`)는 `Document`를 지우면 `models/document.py`에 설정된
  `cascade="all, delete-orphan"`에 의해 `extracted_texts`/`analyses`도 함께 지워집니다.
  (업로드 시 저장한 실제 파일도 `settings.UPLOAD_DIR`에서 함께 삭제하는 것을 잊지 마세요.)

**완료 판단 기준**
- `/docs`에서 `GET /api/documents?q=...&page=1&size=20`이 `PageResponse` 형태(`items, page, size,
  total, total_pages`)로 응답한다.
- `GET /api/documents/{id}`가 추출 텍스트 전문과 analyses 배열을 함께 반환한다.
- `GET /api/documents/{id}/download?format=txt`로 받은 파일의 한글 파일명이 깨지지 않는다.
- `DELETE /api/documents/{id}` 후 같은 id로 상세 조회하면 404가 온다.

---

## 공통 완료 판단 기준 (3명 모두)

- `uvicorn app.main:app --reload` 실행 후 `/docs`에서 자신의 엔드포인트가 노출된다.
- 잘못된 입력(빈 파일, 없는 문서 id 등)에 대해 `ErrorResponse`(`code, message, request_id`)
  형태의 에러가 오고, 서버가 죽지 않는다.
- 테스트 코드는 이번 단계에서 작성하지 않습니다 (별도 일정에서 진행).
