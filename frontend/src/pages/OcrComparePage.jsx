import { useEffect, useState } from 'react'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import EmptyState from '../components/ui/EmptyState'
import Icon from '../components/ui/Icon'
import PageHeader from '../components/ui/PageHeader'
import { compareOcr } from '../api/ocrCompare'
import './OcrComparePage.css'

const ENGINES = ['paddle', 'tesseract', 'easyocr']
const ENGINE_LABELS = { paddle: 'PaddleOCR', tesseract: 'Tesseract', easyocr: 'EasyOCR' }

function formatPercent(value) {
  return value === null || value === undefined ? '-' : `${value.toFixed(1)}%`
}

export default function OcrComparePage() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [groundTruthFile, setGroundTruthFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl])

  function handleFileChange(event) {
    const file = event.target.files?.[0] ?? null
    setSelectedFile(file)
    setResult(null)
    setError(null)
    setPreviewUrl(file?.type.startsWith('image/') ? URL.createObjectURL(file) : null)
  }

  async function handleSubmit(event) {
    event?.preventDefault()
    if (!selectedFile) return
    setLoading(true)
    setError(null)
    try {
      setResult(await compareOcr(selectedFile, groundTruthFile))
    } catch (err) {
      setError(err)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const hasGroundTruth = Boolean(
    result && ENGINES.some((engine) => result[engine].ground_truth_accuracy !== null),
  )
  const accuracyOf = (engineResult) =>
    hasGroundTruth ? engineResult.ground_truth_accuracy : engineResult.avg_confidence
  const fastestMs = result ? Math.min(...ENGINES.map((engine) => result[engine].elapsed_ms)) : null
  const accuracyValues = result
    ? ENGINES.map((engine) => accuracyOf(result[engine])).filter((value) => value != null)
    : []
  const highestAccuracy = accuracyValues.length ? Math.max(...accuracyValues) : null

  return (
    <main className="c-scope ocr-compare">
      <PageHeader
        eyebrow="OCR LAB"
        title="OCR 엔진 비교"
        description="동일한 문서를 세 OCR 엔진으로 처리해 인식 결과, 정확도와 소요 시간을 한눈에 비교합니다."
      />

      <form className="ocr-compare__form" onSubmit={handleSubmit}>
        <label className="ocr-compare__field">
          <span>비교할 문서 <b>필수</b></span>
          <input type="file" accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp,.gif,.pdf,.docx,.hwpx" onChange={handleFileChange} />
          <small>{selectedFile?.name || '이미지, PDF, DOCX, HWPX'}</small>
        </label>
        <label className="ocr-compare__field">
          <span>정답 데이터 <em>선택</em></span>
          <input type="file" accept=".json" onChange={(event) => setGroundTruthFile(event.target.files?.[0] ?? null)} />
          <small>{groundTruthFile?.name || 'LabelMe JSON을 추가하면 실제 정확도를 계산합니다.'}</small>
        </label>
        <button type="submit" className="btn btn--primary ocr-compare__submit" disabled={!selectedFile || loading}>
          <Icon name="compare" size={16} />
          {loading ? '비교 실행 중…' : '엔진 비교 실행'}
        </button>
      </form>

      <ErrorBanner error={error} onRetry={selectedFile ? handleSubmit : undefined} />

      {selectedFile && (
        <section className="ocr-compare__source">
          {previewUrl ? <img src={previewUrl} alt="선택한 문서 미리보기" /> : <Icon name="documents" size={28} />}
          <div><span>선택한 원본</span><strong>{selectedFile.name}</strong></div>
        </section>
      )}

      {loading ? (
        <div className="ocr-compare__loading"><Spinner label="세 가지 OCR 엔진으로 문서를 분석하고 있습니다…" /></div>
      ) : result ? (
        <section className="ocr-compare__results" aria-label="OCR 비교 결과">
          <div className="ocr-compare__result-head"><div><span>COMPARISON RESULT</span><h2>엔진별 분석 결과</h2></div><p>{hasGroundTruth ? '정답 데이터 기준 정확도' : '엔진 confidence 기준'}</p></div>
          <div className="ocr-compare__grid">
            {ENGINES.map((engine) => {
              const engineResult = result[engine]
              const accuracy = accuracyOf(engineResult)
              return (
                <article className="ocr-card" key={engine}>
                  <div className="ocr-card__head"><span>{ENGINE_LABELS[engine]}</span>{accuracy === highestAccuracy && <b>최고 정확도</b>}</div>
                  <dl className="ocr-card__stats">
                    <div><dt>{hasGroundTruth ? '정확도' : 'Confidence'}</dt><dd>{formatPercent(accuracy)}</dd></div>
                    <div><dt>소요 시간</dt><dd>{engineResult.elapsed_ms.toLocaleString()}ms {engineResult.elapsed_ms === fastestMs && <small>가장 빠름</small>}</dd></div>
                    <div><dt>추출 글자</dt><dd>{engineResult.char_count.toLocaleString()}자</dd></div>
                  </dl>
                  {hasGroundTruth && <p className="ocr-card__note">엔진 confidence {formatPercent(engineResult.avg_confidence)}</p>}
                  <pre className="ocr-card__text">{engineResult.text || '(인식된 텍스트 없음)'}</pre>
                </article>
              )
            })}
          </div>
        </section>
      ) : (
        <EmptyState icon="compare" title="비교 결과가 여기에 표시됩니다" description="문서와 선택적으로 정답 데이터를 첨부한 뒤 엔진 비교를 실행하세요." />
      )}
    </main>
  )
}
