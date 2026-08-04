// =============================================================================
// 이 파일의 책임: 같은 이미지를 PaddleOCR과 Tesseract 양쪽에 돌려 정확도(각
//   엔진이 자체 보고하는 인식 신뢰도 평균)와 소요시간을 나란히 비교해서 보여준다.
//   정답 텍스트가 없어 실제 정오 비교는 불가능하므로, "정확도"는 confidence
//   평균을 대용으로 쓴다는 점을 화면에도 명시한다.
// 다른 파일과의 관계: api/ocrCompare.js 의 compareOcr() 을 호출한다.
//   backend/app/api/routes/ocr_compare_router.py 의 POST /api/ocr-compare 와 짝을 이룬다.
// =============================================================================

import { useState } from 'react'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import { compareOcr } from '../api/ocrCompare'
import './OcrComparePage.css'

const ENGINE_LABELS = {
  paddle: 'PaddleOCR',
  tesseract: 'Tesseract',
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
    setPreviewUrl(file ? URL.createObjectURL(file) : null)
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

  // 두 엔진 중 더 나은 쪽에 뱃지를 붙여 한눈에 비교되게 한다.
  const fasterEngine =
    result && result.paddle.elapsed_ms !== result.tesseract.elapsed_ms
      ? (result.paddle.elapsed_ms < result.tesseract.elapsed_ms ? 'paddle' : 'tesseract')
      : null
  const moreConfidentEngine =
    result && result.paddle.avg_confidence !== null && result.tesseract.avg_confidence !== null
      ? (result.paddle.avg_confidence > result.tesseract.avg_confidence ? 'paddle' : 'tesseract')
      : null

  return (
    <div className="c-scope ocr-compare">
      <header className="ocr-compare__head">
        <h1 className="ocr-compare__title">OCR 엔진 비교</h1>
        <p className="ocr-compare__desc">
          같은 이미지를 PaddleOCR과 Tesseract에 동시에 돌려 인식 신뢰도(정확도 대용)와
          소요시간을 비교합니다. 정답 텍스트가 없어 실제 오탈자 비교는 아니며, 각 엔진이
          스스로 보고하는 confidence 평균을 정확도로 표시합니다.
        </p>
      </header>

      <form className="ocr-compare__form" onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".png,.jpg,.jpeg"
          onChange={handleFileChange}
          aria-label="비교할 이미지 선택"
        />
        <button type="submit" className="btn btn--primary" disabled={!selectedFile || loading}>
          {loading ? '비교 실행 중...' : '비교 실행'}
        </button>
      </form>

      {previewUrl && (
        <img className="ocr-compare__preview" src={previewUrl} alt="비교할 이미지 미리보기" />
      )}

      <ErrorBanner error={error} onRetry={selectedFile ? handleSubmit : undefined} />

      {loading && <Spinner label="두 엔진으로 OCR을 실행하는 중입니다…" />}

      {result && !loading && (
        <div className="ocr-compare__grid">
          {['paddle', 'tesseract'].map((engine) => {
            const engineResult = result[engine]
            return (
              <div className="ocr-card" key={engine}>
                <h2 className="ocr-card__title">{ENGINE_LABELS[engine]}</h2>

                <dl className="ocr-card__stats">
                  <div className="ocr-card__stat">
                    <dt>정확도</dt>
                    <dd>
                      {formatConfidence(engineResult.avg_confidence)}
                      {moreConfidentEngine === engine && (
                        <span className="ocr-card__badge">더 정확함</span>
                      )}
                    </dd>
                  </div>
                  <div className="ocr-card__stat">
                    <dt>소요시간</dt>
                    <dd>
                      {engineResult.elapsed_ms.toLocaleString()}ms
                      {fasterEngine === engine && (
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
