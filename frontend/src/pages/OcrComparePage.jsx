// =============================================================================
// 이 파일의 책임: 같은 입력을 PaddleOCR·Tesseract·EasyOCR 세 엔진에 동시에
//   돌려 정확도(각 엔진이 자체 보고하는 인식 신뢰도 평균)와 소요시간을 나란히
//   비교해서 보여준다. 이미지 파일은 그대로, PDF/DOCX/HWPX는 백엔드가 첫
//   페이지(또는 문서 안 첫 그림)를 이미지로 변환한 뒤 비교한다. 정답 텍스트가
//   없어 실제 정오 비교는 불가능하므로, "정확도"는 confidence 평균을 대용으로
//   쓴다는 점을 화면에도 명시한다.
// 다른 파일과의 관계: api/ocrCompare.js 의 compareOcr() 을 호출한다.
//   backend/app/api/routes/ocr_compare_router.py 의 POST /api/ocr-compare 와 짝을 이룬다.
// =============================================================================

import { useState } from 'react'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import { compareOcr } from '../api/ocrCompare'
import './OcrComparePage.css'

const ENGINES = ['paddle', 'tesseract', 'easyocr']

const ENGINE_LABELS = {
  paddle: 'PaddleOCR',
  tesseract: 'Tesseract',
  easyocr: 'EasyOCR',
}

function formatConfidence(value) {
  return value === null || value === undefined ? '—' : `${value.toFixed(1)}%`
}

export default function OcrComparePage() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function handleFileChange(event) {
    const file = event.target.files?.[0] ?? null
    setSelectedFile(file)
    // PDF/DOCX/HWPX는 <img>로 그대로 미리보기가 안 되니, 이미지 파일일 때만 만든다.
    setPreviewUrl(file && file.type.startsWith('image/') ? URL.createObjectURL(file) : null)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!selectedFile) return

    setLoading(true)
    setError(null)
    try {
      setResult(await compareOcr(selectedFile))
    } catch (err) {
      setError(err)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  // 엔진들 중 가장 나은 값에 뱃지를 붙여 한눈에 비교되게 한다. (동률이면 전부 표시)
  const fastestMs = result
    ? Math.min(...ENGINES.map((engine) => result[engine].elapsed_ms))
    : null
  const confidenceValues = result
    ? ENGINES.map((engine) => result[engine].avg_confidence).filter(
        (value) => value !== null && value !== undefined,
      )
    : []
  const highestConfidence = confidenceValues.length ? Math.max(...confidenceValues) : null

  return (
    <div className="c-scope ocr-compare">
      <header className="ocr-compare__head">
        <h1 className="ocr-compare__title">OCR 엔진 비교</h1>
        <p className="ocr-compare__desc">
          같은 파일을 PaddleOCR·Tesseract·EasyOCR 세 엔진에 동시에 돌려 인식
          신뢰도(정확도 대용)와 소요시간을 비교합니다. 이미지는 그대로, PDF/DOCX/HWPX는
          첫 페이지(또는 문서 안 첫 그림)를 이미지로 변환해 비교합니다. 정답 텍스트가 없어
          실제 오탈자 비교는 아니며, 각 엔진이 스스로 보고하는 confidence 평균을 정확도로
          표시합니다.
        </p>
      </header>

      <form className="ocr-compare__form" onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp,.gif,.pdf,.docx,.hwpx"
          onChange={handleFileChange}
          aria-label="비교할 파일 선택"
        />
        <button type="submit" className="btn btn--primary" disabled={!selectedFile || loading}>
          {loading ? '비교 실행 중...' : '비교 실행'}
        </button>
      </form>

      {previewUrl ? (
        <img className="ocr-compare__preview" src={previewUrl} alt="비교할 이미지 미리보기" />
      ) : (
        selectedFile && <p className="ocr-compare__filename">선택한 파일: {selectedFile.name}</p>
      )}

      <ErrorBanner error={error} onRetry={selectedFile ? handleSubmit : undefined} />

      {loading && <Spinner label="세 엔진으로 OCR을 실행하는 중입니다…" />}

      {result && !loading && (
        <div className="ocr-compare__grid">
          {ENGINES.map((engine) => {
            const engineResult = result[engine]
            return (
              <div className="ocr-card" key={engine}>
                <h2 className="ocr-card__title">{ENGINE_LABELS[engine]}</h2>

                <dl className="ocr-card__stats">
                  <div className="ocr-card__stat">
                    <dt>정확도</dt>
                    <dd>
                      {formatConfidence(engineResult.avg_confidence)}
                      {highestConfidence !== null &&
                        engineResult.avg_confidence === highestConfidence && (
                          <span className="ocr-card__badge">더 정확함</span>
                        )}
                    </dd>
                  </div>
                  <div className="ocr-card__stat">
                    <dt>소요시간</dt>
                    <dd>
                      {engineResult.elapsed_ms.toLocaleString()}ms
                      {engineResult.elapsed_ms === fastestMs && (
                        <span className="ocr-card__badge">더 빠름</span>
                      )}
                    </dd>
                  </div>
                  <div className="ocr-card__stat">
                    <dt>추출 글자 수</dt>
                    <dd>{engineResult.char_count.toLocaleString()}자</dd>
                  </div>
                </dl>

                <pre className="ocr-card__text">
                  {engineResult.text || '(인식된 텍스트 없음)'}
                </pre>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
