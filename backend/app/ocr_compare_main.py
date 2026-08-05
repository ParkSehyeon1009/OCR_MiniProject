# =============================================================================
# 이 파일의 책임: OCR 비교 화면(POST /api/ocr-compare) 전용 FastAPI 앱 진입점.
#   Tesseract/EasyOCR(+PyTorch)처럼 무거운 의존성을 메인 API(app/main.py)의
#   프로세스와 완전히 분리하기 위해 별도 ASGI 앱으로 둔다 — 이 기능을 한 번도
#   안 써도 메인 API가 이 무게를 짊어지지 않는다. DB를 전혀 쓰지 않으므로
#   lifespan에서 테이블 생성도 하지 않는다.
# 다른 파일과의 관계: ocr_compare_dependencies.py의 provider들을 쓰는
#   api/routes/ocr_compare_router.py 하나만 등록한다. 예외 핸들러·request_id
#   미들웨어는 core/*(메인 API와 공유하는 코드)를 그대로 재사용한다.
# 실행: uvicorn app.ocr_compare_main:app --port 8001 (docker-compose.yml의
#   ocr-compare 서비스가 이 명령으로 띄운다 — 이미지는 메인 api와 공유한다).
# =============================================================================

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import ocr_compare_router
from app.core.config import settings
from app.core.exceptions import (
    BusinessError,
    business_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.logging_config import setup_logging
from app.core.middleware import RequestIdMiddleware

setup_logging()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)

app.add_exception_handler(BusinessError, business_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ocr_compare_router.router)
