import { useEffect, useState } from 'react'
import { analyzeDocument, checkHealth, uploadDocument } from '../api/client'
import './TestPage.css'

const ANALYZER_TYPES = ['summary', 'category']

// analyzer_type마다 result의 구조가 달라서(§7 result: dict), 아는 형태는 보기 좋게
// 풀어서 보여주고 모르는 형태(향후 추가될 analyzer)는 원본 JSON으로 안전하게 대체 표시한다.
function renderAnalysisResult(analysis) {
  const { analyzer_type, result } = analysis

  if (analyzer_type === 'summary' && typeof result?.summary === 'string') {
    return <p className="result-text">{result.summary}</p>
  }

  if (analyzer_type === 'category' && typeof result?.category === 'string') {
    return (
      <div className="result-category">
        <span className="category-chip">{result.category}</span>
        {result.reason && <p className="category-reason">{result.reason}</p>}
      </div>
    )
  }

  return <pre className="result-raw">{JSON.stringify(result, null, 2)}</pre>
}

function TestPage() {
  const [health, setHealth] = useState('checking...')
  const [selectedFile, setSelectedFile] = useState(null)
  const [document, setDocument] = useState(null)
  const [analyses, setAnalyses] = useState([])
  const [checkedTypes, setCheckedTypes] = useState({ summary: true, category: true })
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    checkHealth()
      .then(() => setHealth('ok'))
      .catch(() => setHealth('unreachable'))
  }, [])

  function toggleType(type) {
    setCheckedTypes((prev) => ({ ...prev, [type]: !prev[type] }))
  }

  async function handleUpload(event) {
    event.preventDefault()
    if (!selectedFile) return

    setUploading(true)
    setError(null)
    try {
      const result = await uploadDocument(selectedFile)
      setDocument(result)
      setAnalyses([])
    } catch (err) {
      setError(err)
    } finally {
      setUploading(false)
    }
  }

  async function handleAnalyze() {
    if (!document) return

    const types = ANALYZER_TYPES.filter((type) => checkedTypes[type])

    setAnalyzing(true)
    setError(null)
    try {
      const result = await analyzeDocument(document.id, types.length ? types : null)
      setAnalyses((prev) => [...result.analyses, ...prev])
    } catch (err) {
      setError(err)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="test-page">
      <h1>PDF Brief AI — Test Page</h1>
      <p className="subtitle">backend health: {health}</p>

      {error && (
        <div className="error-banner">
          {error.code ? `[${error.code}] ` : ''}
          {error.message}
        </div>
      )}

      <section>
        <h2>1. 문서 업로드</h2>
        <form className="row" onSubmit={handleUpload}>
          <input
            type="file"
            accept=".pdf,.docx,.hwpx,.png,.jpg,.jpeg"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
          <button type="submit" disabled={!selectedFile || uploading}>
            {uploading ? '업로드 중...' : '업로드'}
          </button>
        </form>

        {document ? (
          <div className="doc-card">
            <dl>
              <dt>id</dt>
              <dd>{document.id}</dd>
              <dt>filename</dt>
              <dd>{document.filename}</dd>
              <dt>file_type</dt>
              <dd>{document.file_type}</dd>
              <dt>document_type</dt>
              <dd>{document.document_type}</dd>
              <dt>status</dt>
              <dd>{document.status}</dd>
              <dt>page_count</dt>
              <dd>{document.page_count}</dd>
              <dt>char_count</dt>
              <dd>{document.char_count}</dd>
              <dt>extract_method</dt>
              <dd>{document.extract_method}</dd>
              <dt>created_at</dt>
              <dd>{document.created_at}</dd>
            </dl>
          </div>
        ) : (
          <p className="empty">아직 업로드된 문서가 없습니다.</p>
        )}
      </section>

      <section>
        <h2>2. 분석 실행</h2>
        <div className="row">
          {ANALYZER_TYPES.map((type) => (
            <label key={type} className="checkbox">
              <input
                type="checkbox"
                checked={checkedTypes[type]}
                onChange={() => toggleType(type)}
              />
              {type}
            </label>
          ))}
          <button type="button" onClick={handleAnalyze} disabled={!document || analyzing}>
            {analyzing ? '분석 중...' : '분석 실행'}
          </button>
        </div>

        {analyses.length > 0 ? (
          analyses.map((analysis) => (
            <div className="analysis-card" key={analysis.id}>
              <div className="analysis-header">
                <span className={`type-badge type-${analysis.analyzer_type}`}>
                  {analysis.analyzer_type}
                </span>
                <span className="analysis-source">
                  #{analysis.id} · {analysis.provider}/{analysis.model_name}
                </span>
              </div>

              <div className="analysis-body">{renderAnalysisResult(analysis)}</div>

              <div className="analysis-footer">
                <span>tokens {analysis.tokens_in ?? '-'}→{analysis.tokens_out ?? '-'}</span>
                <span>{analysis.latency_ms ?? '-'}ms</span>
                <span>{analysis.created_at}</span>
              </div>
            </div>
          ))
        ) : (
          <p className="empty">아직 분석 결과가 없습니다.</p>
        )}
      </section>
    </div>
  )
}

export default TestPage
