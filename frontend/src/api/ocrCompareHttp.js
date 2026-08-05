import { createApiClient } from './createApiClient'

// OCR 비교(/api/ocr-compare)는 Tesseract/EasyOCR(+PyTorch)처럼 무거운
// 의존성을 메인 API 프로세스와 분리하기 위해 별도 서비스(다른 포트)로 떠 있다.
// backend/app/ocr_compare_main.py, docker-compose.yml의 ocr-compare 서비스와 짝을 이룬다.
const OCR_COMPARE_BASE_URL =
  import.meta.env.VITE_OCR_COMPARE_BASE_URL || 'http://localhost:8001'

export const ocrCompareHttp = createApiClient(OCR_COMPARE_BASE_URL)
