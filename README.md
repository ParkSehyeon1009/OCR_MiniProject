# OCR_MiniProject

문서를 업로드하면 **텍스트를 추출(OCR)** 하고, **AI가 카테고리 분류·요약**까지 수행하는 풀스택 문서 분석 애플리케이션입니다.
PDF·DOCX·HWPX·이미지 등 다양한 형식을 지원하며, 여러 OCR 엔진(PaddleOCR·Tesseract·EasyOCR)의 인식 결과를 비교하는 기능도 제공합니다.

## 주요 기능

- 📄 **다양한 문서 업로드** — PDF, DOCX, HWPX, 이미지(PNG/JPG 등) 지원
- 🔍 **텍스트 추출(OCR)** — 형식별 전용 추출기 + 이미지 OCR 엔진 자동 선택
- ⚖️ **OCR 엔진 비교** — PaddleOCR / Tesseract / EasyOCR 결과를 나란히 비교하고, 정답(ground truth) 대비 정확도 측정
- 🤖 **AI 문서 분석** — 카테고리 분류 및 요약 생성 (OpenAI `gpt-4o-mini`)
- 📥 **결과 관리** — 문서 목록·검색·상세 조회, 요약 텍스트 다운로드, 삭제
- 🧪 **Fake AI 모드** — API 비용 없이 개발/테스트 가능 (기본값)

## 기술 스택

| 영역 | 기술 |
|------|------|
| **Frontend** | React 19, Vite, React Router, Axios |
| **Backend** | Python, FastAPI, Uvicorn, Pydantic |
| **Database** | PostgreSQL 16, SQLAlchemy |
| **OCR / 문서 처리** | PaddleOCR, Tesseract(pytesseract), EasyOCR, PyMuPDF, python-docx, OpenCV, Pillow |
| **AI** | OpenAI API |
| **Infra** | Docker, Docker Compose |

## 프로젝트 구조

```
OCR_MiniProject/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI 진입점
│       ├── api/routes/          # 업로드 · 문서 · 분석 · OCR 비교 라우터
│       ├── extractors/          # PDF · DOCX · HWPX · 이미지 OCR 추출기
│       ├── analyzers/           # 카테고리 분류 · 요약 분석기
│       ├── services/            # 비즈니스 로직
│       ├── repositories/        # DB 접근 계층
│       ├── models/ · schemas/   # ORM 모델 · 요청/응답 스키마
│       └── core/                # 설정 · 예외 · 미들웨어 · 로깅
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── pages/               # 메인 · 목록 · 상세 · OCR 비교 페이지
        ├── components/          # 공통 UI 컴포넌트
        └── api/                 # 백엔드 API 클라이언트
```

## 시작하기

### Docker로 실행 (권장)

```bash
# 저장소 클론
git clone https://github.com/ParkSehyeon1009/OCR_MiniProject.git
cd OCR_MiniProject

# 환경변수 파일 준비
cp backend/.env.example backend/.env

# 전체 서비스 빌드 및 실행
docker compose up --build
```

실행 후 접속 주소:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs

### 로컬에서 개별 실행

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

> 로컬 실행 시 PostgreSQL이 별도로 필요합니다. `backend/.env`의 `DATABASE_URL`을 사용 중인 DB에 맞게 설정하세요.

## 환경변수

`backend/.env.example`를 복사해 `backend/.env`를 만들고 값을 채워주세요.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/pdfbrief` | PostgreSQL 연결 문자열 |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | 허용 origin (콤마 구분) |
| `USE_FAKE_AI` | `true` | `true`면 실제 API 호출 없이 가짜 응답 사용 (비용 방지) |
| `API_KEY` | *(없음)* | OpenAI API 키 (`USE_FAKE_AI=false`일 때 필요) |
| `AI_MODEL` | `gpt-4o-mini` | 사용할 AI 모델 |
| `AI_TIMEOUT_SECONDS` | `60` | AI 요청 타임아웃(초) |
| `UPLOAD_DIR` | `./uploads` | 업로드 파일 저장 경로 |
| `MAX_FILE_SIZE_MB` | `10` | 최대 업로드 크기(MB) |
| `MAX_PAGES` | `30` | 최대 처리 페이지 수 |
| `MAX_EXTRACTED_CHARS` | `45000` | 최대 추출 문자 수 |
| `ENVIRONMENT` | `development` | 실행 환경 |

> ⚠️ 실제 OpenAI API를 사용하려면 `USE_FAKE_AI=false`로 바꾸고 `API_KEY`를 설정하세요. 기본값 `true`는 의도치 않은 과금을 막기 위한 안전장치입니다.

## API 엔드포인트

기본 prefix: `/api`

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/documents` | 문서 업로드 및 텍스트 추출 |
| `GET` | `/api/documents` | 문서 목록 조회 (검색·필터·페이지네이션) |
| `GET` | `/api/documents/{document_id}` | 문서 상세 조회 (추출 텍스트·분석 결과 포함) |
| `GET` | `/api/documents/{document_id}/download` | 요약 결과 텍스트 파일 다운로드 |
| `DELETE` | `/api/documents/{document_id}` | 문서 및 관련 데이터 삭제 |
| `POST` | `/api/documents/{document_id}/analyze` | 문서 AI 분석 (카테고리 분류·요약) |
| `POST` | `/api/ocr-compare` | 이미지에 대해 여러 OCR 엔진 결과 비교 및 정확도 측정 |
| `GET` | `/health` | 헬스 체크 |

전체 명세는 실행 후 [Swagger UI](http://localhost:8000/docs)에서 확인할 수 있습니다.
