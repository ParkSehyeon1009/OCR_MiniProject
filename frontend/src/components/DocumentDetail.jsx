// =============================================================================
// 이 파일의 책임: 문서 1건의 상세 정보를 그린다 — 메타 정보, 요약, 분류 근거,
//   추출 원문(접기/펼치기), 분석 이력(provider·model·tokens·latency).
//   API 를 직접 호출하지 않는 표현 전용 컴포넌트이며, 데이터와 동작(다운로드·
//   분석 실행)은 모두 props 로 받는다.
// 다른 파일과의 관계: pages/DetailPage.jsx 가 GET /api/documents/{id} 응답을
//   그대로 document prop 으로 넘긴다. 필드명은 backend/app/schemas/document.py
//   의 DocumentDetailResponse 와 1:1 로 대응한다. Badge 로 상태·카테고리를 그린다.
//   API 를 안 쓰기 때문에 목록 화면(안1)에서 우측 패널로 재사용할 수도 있다.
// Spring 비교: 로직이 없는 JSP/Thymeleaf 뷰 조각에 해당. 조회·가공은 호출하는
//   쪽(DetailPage = Controller 역할)이 끝내고 완성된 데이터만 내려준다.
// =============================================================================

import { useState } from 'react'
import Badge from './Badge'
import { formatDateTime, formatNumber, formatLatency } from '../utils/format'
import './DocumentDetail.css'

// 원문을 접은 상태에서 보여줄 글자 수. 45,000자까지 올 수 있어 기본은 접어둔다.
const PREVIEW_CHARS = 700

/**
 * analyses 배열에서 특정 analyzer_type 의 최신 항목을 고른다.
 * 백엔드가 재분석을 허용하므로 같은 타입이 여러 건 쌓일 수 있다.
 * (백엔드 _build_list_row 의 get_latest_by_type 과 같은 규칙)
 */
function pickLatest(analyses, analyzerType) {
  const matched = (analyses || []).filter((a) => a.analyzer_type === analyzerType)
  if (matched.length === 0) return null

  return matched.reduce((latest, current) =>
    new Date(current.created_at) >= new Date(latest.created_at) ? current : latest
  )
}

export default function DocumentDetail({ 
  document,
  onAnalyze,
  onDownload,
  onDelete,
  analyzing = false,
  deleting = false,
}) 
{
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
      {/* ---------------------------------------------------------- 헤더 */}
      <header className="doc-detail__head">
        <div className="doc-detail__title-row">
          {/* 파일명이 길어도 레이아웃이 밀리지 않도록 CSS 에서 줄바꿈 처리 */}
          <h2 className="doc-detail__filename" title={document.filename}>
            {document.filename}
          </h2>

          <div className="doc-detail__actions">
            {/* 분석 전 문서에만 분석 버튼을 노출한다 (A/B 파트 엔드포인트 호출) */}
            {onAnalyze && !hasAnalysis && (
              <button
                type="button"
                className="btn btn--primary"
                onClick={onAnalyze}
                disabled={analyzing}
              >
                {analyzing ? '분석 중…' : 'AI 분석 실행'}
              </button>
            )}
            {/* 요약이 없으면 다운로드할 내용이 없으므로 비활성화한다.
                (백엔드도 NOT_EXTRACTED_YET 으로 막지만, 미리 막는 편이 친절하다) */}
            {onDownload && (
              <button
                type="button"
                className="btn"
                onClick={onDownload}
                disabled={!hasAnalysis}
                title={hasAnalysis ? '' : '분석을 먼저 실행해야 합니다'}
              >
                요약 .txt 다운로드
              </button>
            )}
            {onDelete && (
              <button
                type="button"
                className="btn btn--danger"
                onClick={onDelete}
                disabled={deleting}
              >
                {deleting ? '삭제 중…' : '삭제'}
              </button>
            )}

          </div>
        </div>

        <div className="doc-detail__badges">
          <Badge variant="category" value={category} />
          <Badge variant="status" value={document.status} />
          <Badge variant="method" value={document.extract_method} />
        </div>
      </header>

      {/* ------------------------------------------------------ 메타 정보 */}
      <dl className="doc-detail__meta">
        <div>
          <dt>유형</dt>
          <dd>{document.document_type || '-'}</dd>
        </div>
        <div>
          <dt>형식</dt>
          <dd>{document.file_type || '-'}</dd>
        </div>
        <div>
          <dt>페이지</dt>
          <dd>{document.page_count ? `${formatNumber(document.page_count)}p` : '-'}</dd>
        </div>
        <div>
          <dt>글자 수</dt>
          <dd>{document.char_count ? `${formatNumber(document.char_count)}자` : '-'}</dd>
        </div>
        <div>
          <dt>업로드</dt>
          <dd>{formatDateTime(document.created_at)}</dd>
        </div>
      </dl>

      {/* ---------------------------------------------------------- 요약 */}
      <section className="doc-detail__section">
        <h3 className="doc-detail__section-title">AI 요약</h3>
        {summary ? (
          <p className="doc-detail__summary">{summary}</p>
        ) : (
          <p className="doc-detail__empty">
            아직 분석되지 않았습니다. 위의 &lsquo;AI 분석 실행&rsquo;을 눌러 주세요.
          </p>
        )}
      </section>

      {/* ------------------------------------------------------ 분류 근거 */}
      {reason && (
        <section className="doc-detail__section">
          <h3 className="doc-detail__section-title">분류 근거</h3>
          <p className="doc-detail__reason">{reason}</p>
        </section>
      )}

      {/* ------------------------------------------------- 추출 원문 */}
      <section className="doc-detail__section">
        <h3 className="doc-detail__section-title">
          추출 원문
          {extractedText && (
            <span className="doc-detail__count">
              {formatNumber(extractedText.length)}자
            </span>
          )}
        </h3>

        {extractedText ? (
          <>
            <pre
              className={
                textExpanded
                  ? 'doc-detail__text doc-detail__text--expanded'
                  : 'doc-detail__text'
              }
            >
              {textExpanded || !isLongText
                ? extractedText
                : `${extractedText.slice(0, PREVIEW_CHARS)}…`}
            </pre>

            {isLongText && (
              <button
                type="button"
                className="doc-detail__toggle"
                onClick={() => setTextExpanded((prev) => !prev)}
                aria-expanded={textExpanded}
              >
                {textExpanded ? '접기' : '전체 보기'}
              </button>
            )}
          </>
        ) : (
          <p className="doc-detail__empty">추출된 텍스트가 없습니다.</p>
        )}
      </section>

      {/* ------------------------------------------------------ 분석 이력 */}
      {hasAnalysis && (
        <section className="doc-detail__section">
          <h3 className="doc-detail__section-title">분석 이력</h3>
          <div className="doc-detail__table-wrap">
            <table className="doc-detail__table">
              <thead>
                <tr>
                  <th>분석기</th>
                  <th>제공자 / 모델</th>
                  <th className="num">토큰(입력/출력)</th>
                  <th className="num">응답 시간</th>
                  <th>실행 일시</th>
                </tr>
              </thead>
              <tbody>
                {document.analyses.map((item) => (
                  <tr key={item.id}>
                    <td>{item.analyzer_type}</td>
                    <td>
                      <span className="doc-detail__provider">{item.provider}</span>
                      <span className="doc-detail__model">{item.model_name}</span>
                    </td>
                    <td className="num">
                      {formatNumber(item.tokens_in)} / {formatNumber(item.tokens_out)}
                    </td>
                    <td className="num">{formatLatency(item.latency_ms)}</td>
                    <td>{formatDateTime(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* latency_ms 는 MAX_EXTRACTED_CHARS(45,000) 값을 실측 조정할 때
              근거 자료로 쓴다 (D5 테스트 항목). */}
        </section>
      )}
    </article>
  )
}
