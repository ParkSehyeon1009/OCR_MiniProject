import { useState } from 'react'
import Badge from './Badge'
import Icon from './ui/Icon'
import { formatDateTime, formatNumber, formatLatency } from '../utils/format'
import './DocumentDetail.css'

const PREVIEW_CHARS = 700

function pickLatest(analyses, analyzerType) {
  const matched = (analyses || []).filter((item) => item.analyzer_type === analyzerType)
  if (matched.length === 0) return null

  return matched.reduce((latest, current) =>
    new Date(current.created_at) >= new Date(latest.created_at) ? current : latest,
  )
}

export default function DocumentDetail({
  document,
  onAnalyze,
  onDownload,
  onDelete,
  analyzing = false,
  deleting = false,
}) {
  const [textExpanded, setTextExpanded] = useState(false)

  if (!document) return null

  const summaryAnalysis = pickLatest(document.analyses, 'summary')
  const categoryAnalysis = pickLatest(document.analyses, 'category')
  const summary = summaryAnalysis?.result?.summary || null
  const category = categoryAnalysis?.result?.category || null
  const reason = categoryAnalysis?.result?.reason || null
  const hasAnalysis = Boolean(summaryAnalysis || categoryAnalysis)
  const extractedText = document.extracted_text || ''
  const isLongText = extractedText.length > PREVIEW_CHARS

  return (
    <article className="doc-detail">
      <header className="doc-detail__head">
        <div className="doc-detail__heading">
          <span className="doc-detail__eyebrow">DOCUMENT DETAIL</span>
          <h1 className="doc-detail__filename" title={document.filename}>
            {document.filename}
          </h1>
          <div className="doc-detail__badges">
            <Badge variant="category" value={category} />
            <Badge variant="status" value={document.status} />
            <Badge variant="method" value={document.extract_method} />
          </div>
        </div>

        <div className="doc-detail__actions">
          {onAnalyze && !hasAnalysis && (
            <button type="button" className="btn btn--primary" onClick={onAnalyze} disabled={analyzing}>
              <Icon name="sparkles" size={16} />
              {analyzing ? '분석 중…' : 'AI 분석 실행'}
            </button>
          )}
          {onDownload && (
            <button
              type="button"
              className="btn btn--secondary"
              onClick={onDownload}
              disabled={!hasAnalysis}
              title={hasAnalysis ? '' : '분석을 먼저 실행해야 합니다.'}
            >
              요약 다운로드
            </button>
          )}
          {onDelete && (
            <button type="button" className="btn btn--danger" onClick={onDelete} disabled={deleting}>
              {deleting ? '삭제 중…' : '삭제'}
            </button>
          )}
        </div>
      </header>

      <dl className="doc-detail__meta">
        <div><dt>문서 유형</dt><dd>{document.document_type || '-'}</dd></div>
        <div><dt>파일 형식</dt><dd>{document.file_type || '-'}</dd></div>
        <div><dt>페이지</dt><dd>{document.page_count ? `${formatNumber(document.page_count)}p` : '-'}</dd></div>
        <div><dt>글자 수</dt><dd>{document.char_count ? `${formatNumber(document.char_count)}자` : '-'}</dd></div>
        <div><dt>업로드 일시</dt><dd>{formatDateTime(document.created_at)}</dd></div>
      </dl>

      <div className="doc-detail__content-grid">
        <section className="doc-detail__section doc-detail__section--summary">
          <div className="doc-detail__section-head">
            <span className="doc-detail__section-icon"><Icon name="sparkles" size={17} /></span>
            <h2>AI 요약</h2>
          </div>
          {summary ? (
            <p className="doc-detail__summary">{summary}</p>
          ) : (
            <p className="doc-detail__empty">아직 분석 결과가 없습니다. AI 분석을 실행해 주세요.</p>
          )}
        </section>

        {reason && (
          <section className="doc-detail__section">
            <div className="doc-detail__section-head">
              <span className="doc-detail__section-icon"><Icon name="check" size={17} /></span>
              <h2>분류 근거</h2>
            </div>
            <p className="doc-detail__reason">{reason}</p>
          </section>
        )}

        <section className="doc-detail__section doc-detail__section--wide">
          <div className="doc-detail__section-head">
            <span className="doc-detail__section-icon"><Icon name="documents" size={17} /></span>
            <h2>추출 원문</h2>
            {extractedText && <span className="doc-detail__count">{formatNumber(extractedText.length)}자</span>}
          </div>

          {extractedText ? (
            <>
              <pre className={`doc-detail__text${textExpanded ? ' doc-detail__text--expanded' : ''}`}>
                {textExpanded || !isLongText ? extractedText : `${extractedText.slice(0, PREVIEW_CHARS)}…`}
              </pre>
              {isLongText && (
                <button
                  type="button"
                  className="doc-detail__toggle"
                  onClick={() => setTextExpanded((prev) => !prev)}
                  aria-expanded={textExpanded}
                >
                  {textExpanded ? '접기' : '전체 원문 보기'}
                </button>
              )}
            </>
          ) : (
            <p className="doc-detail__empty">추출된 텍스트가 없습니다.</p>
          )}
        </section>

        {hasAnalysis && (
          <section className="doc-detail__section doc-detail__section--wide">
            <div className="doc-detail__section-head">
              <span className="doc-detail__section-icon"><Icon name="shield" size={17} /></span>
              <h2>분석 이력</h2>
            </div>
            <div className="doc-detail__table-wrap">
              <table className="doc-detail__table">
                <thead><tr><th>분석기</th><th>제공자 / 모델</th><th className="num">토큰(입력/출력)</th><th className="num">응답 시간</th><th>실행 일시</th></tr></thead>
                <tbody>
                  {(document.analyses || []).map((item) => (
                    <tr key={item.id}>
                      <td>{item.analyzer_type}</td>
                      <td><span className="doc-detail__provider">{item.provider}</span><span className="doc-detail__model">{item.model_name}</span></td>
                      <td className="num">{formatNumber(item.tokens_in)} / {formatNumber(item.tokens_out)}</td>
                      <td className="num">{formatLatency(item.latency_ms)}</td>
                      <td>{formatDateTime(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </article>
  )
}
