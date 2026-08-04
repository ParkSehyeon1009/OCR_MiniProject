// =============================================================================
// 이 파일의 책임: 문서 목록 화면. 검색어·카테고리·페이지 조건으로
//   GET /api/documents 를 호출해 표로 보여주고, 행을 선택하면 우측 패널에
//   상세를 함께 표시한다(마스터-디테일). 조회 조건과 선택된 문서를 모두
//   URL 쿼리스트링에 보관하여, 새로고침·뒤로가기·주소 공유 시 화면이 재현된다.
// 다른 파일과의 관계: api/document.js 의 listDocuments / getDocument /
//   analyzeDocument / downloadSummary 를 호출한다. 우측 패널은
//   components/DocumentDetail 을 그대로 재사용한다 — 그 컴포넌트가 API 를
//   호출하지 않고 props 만 받도록 만들어져 있어 수정 없이 끼울 수 있다.
//   전체 화면 상세(pages/DetailPage)는 그대로 유지된다.
// Spring 비교: Controller 가 목록과 단건을 각각 조회해 하나의 뷰에 담는 것과
//   같다. 조회 조건은 @RequestParam 대신 브라우저 URL 이 보관한다.
// =============================================================================

import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import Badge from '../components/Badge'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import DocumentDetail from '../components/DocumentDetail'
import {
  listDocuments,
  getDocument,
  analyzeDocument,
  downloadSummary,
} from '../api/document'
import { formatDateShort } from '../utils/format'
import './ListPage.css'

// prompts.py 의 CATEGORY_CANDIDATES 와 동일하게 유지해야 한다.
const CATEGORIES = ['계약서', '보고서', '회의록', '공지사항', '메뉴얼', '기타']

const PAGE_SIZE = 20

export default function ListPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  // URL 이 유일한 진실이다. state 로 중복 보관하지 않는다.
  const q = searchParams.get('q') || ''
  const category = searchParams.get('category') || ''
  const page = Number(searchParams.get('page') || 1)
  const selectedId = searchParams.get('selected') || ''

  // 입력 중인 검색어만 로컬 state 로 둔다 (제출 시 URL 로 승격).
  const [keyword, setKeyword] = useState(q)

  // --- 목록 ---
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  // --- 우측 패널(상세) ---
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  // 뒤로가기 등으로 URL 이 바뀌면 입력창도 따라가게 한다.
  useEffect(() => {
    setKeyword(q)
  }, [q])

  // ------------------------------------------------------------ 목록 조회
  useEffect(() => {
    // 조건이 빠르게 연달아 바뀔 때, 먼저 보낸 요청이 늦게 도착해
    // 최신 결과를 덮어쓰는 것을 막는다.
    let discarded = false

    setLoading(true)
    setError(null)

    listDocuments({ q, category, page, size: PAGE_SIZE })
      .then((result) => {
        if (!discarded) setData(result)
      })
      .catch((err) => {
        if (!discarded) setError(err)
      })
      .finally(() => {
        if (!discarded) setLoading(false)
      })

    return () => {
      discarded = true
    }
  }, [q, category, page, reloadKey])

  // ------------------------------------------------------------ 상세 조회
  const loadDetail = useCallback(async () => {
    if (!selectedId) {
      setDetail(null)
      setDetailError(null)
      return
    }

    setDetailLoading(true)
    setDetailError(null)
    setActionError(null)

    try {
      setDetail(await getDocument(selectedId))
    } catch (err) {
      setDetailError(err)
    } finally {
      setDetailLoading(false)
    }
  }, [selectedId])

  useEffect(() => {
    loadDetail()
  }, [loadDetail])

  // -------------------------------------------------------- URL 파라미터
  /** 현재 검색 조건만 담은 파라미터 객체. 빈 값은 제외해 주소를 깔끔히 유지한다. */
  function baseParams() {
    const params = {}
    if (q) params.q = q
    if (category) params.category = category
    if (page > 1) params.page = String(page)
    return params
  }

  /** 조회 조건 변경. selected 를 넘기지 않으므로 조건이 바뀌면 패널이 닫힌다. */
  function applyParams(next) {
    const merged = { q, category, page: 1, ...next }
    const params = {}

    if (merged.q) params.q = merged.q
    if (merged.category) params.category = merged.category
    if (merged.page > 1) params.page = String(merged.page)

    setSearchParams(params)
  }

  function selectDocument(id) {
    setSearchParams({ ...baseParams(), selected: String(id) })
  }

  function closePanel() {
    setSearchParams(baseParams())
  }

  function handleSubmit(event) {
    event.preventDefault() // 폼 기본 동작(새로고침)을 막는다
    applyParams({ q: keyword.trim() })
  }

  function handleReset() {
    setKeyword('')
    setSearchParams({})
  }

  // ------------------------------------------------------------ 패널 동작
  async function handleAnalyze() {
    setAnalyzing(true)
    setActionError(null)
    try {
      await analyzeDocument(selectedId)
      setDetail(await getDocument(selectedId))
      // 분석 결과가 목록의 카테고리·요약 미리보기에도 반영되므로 목록을 다시 읽는다.
      setReloadKey((n) => n + 1)
    } catch (err) {
      setActionError(err)
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleDownload() {
    setActionError(null)
    try {
      await downloadSummary(selectedId, `${detail.filename}_요약.txt`)
    } catch (err) {
      setActionError(err)
    }
  }

  const items = data?.items || []
  const totalPages = data?.total_pages || 0
  const hasFilter = Boolean(q || category)
  const panelOpen = Boolean(selectedId)

  return (
    <div className="c-scope list-page">
      <header className="list-page__head">
        <div>
          <h1 className="list-page__title">문서 목록</h1>
          {data && (
            <p className="list-page__total">
              전체 <strong>{data.total}</strong>건
              {hasFilter && ' (검색 결과)'}
            </p>
          )}
        </div>
        <Link to="/upload" className="list-page__upload-link">
          새 문서 업로드
        </Link>
      </header>

      {/* ------------------------------------------------------- 검색 영역 */}
      <form className="list-page__search" onSubmit={handleSubmit} role="search">
        <input
          type="search"
          className="list-page__input"
          placeholder="파일명 또는 본문 내용 검색"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          aria-label="검색어"
        />

        <select
          className="list-page__select"
          value={category}
          // 카테고리는 즉시 반영한다 (선택 자체가 확정된 의도이므로)
          onChange={(e) => applyParams({ category: e.target.value })}
          aria-label="카테고리"
        >
          <option value="">전체 카테고리</option>
          {CATEGORIES.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>

        <button type="submit" className="btn btn--primary">
          검색
        </button>
        {hasFilter && (
          <button type="button" className="btn" onClick={handleReset}>
            초기화
          </button>
        )}
      </form>

      <ErrorBanner error={error} onRetry={() => setReloadKey((n) => n + 1)} />

      {loading ? (
        <Spinner label="문서를 불러오는 중입니다…" />
      ) : (
        !error && (
          <div
            className={
              panelOpen
                ? 'list-page__split list-page__split--open'
                : 'list-page__split'
            }
          >
            {/* ------------------------------------------------ 좌: 표 */}
            <div className="list-page__main">
              <div className="list-page__table-wrap">
                <table className="list-table">
                  <thead>
                    <tr>
                      <th className="col-name">파일명</th>
                      <th className="col-cat">카테고리</th>
                      <th className="col-sum">요약</th>
                      <th className="col-status">상태</th>
                      <th className="col-date">업로드</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.length === 0 ? (
                      <tr>
                        {/* 검색 결과 없음과 데이터 없음을 구분해 안내한다 */}
                        <td colSpan={5} className="list-table__empty">
                          {hasFilter
                            ? '조건에 맞는 문서가 없습니다.'
                            : '업로드된 문서가 없습니다. 먼저 문서를 업로드해 주세요.'}
                        </td>
                      </tr>
                    ) : (
                      items.map((item) => (
                        <tr
                          key={item.id}
                          className={
                            String(item.id) === selectedId
                              ? 'list-table__row--selected'
                              : undefined
                          }
                        >
                          <td className="col-name">
                            {/* 클릭 시 이동이 아니라 우측 패널에 표시한다 */}
                            <button
                              type="button"
                              className="list-table__link"
                              onClick={() => selectDocument(item.id)}
                            >
                              {item.filename}
                            </button>
                            <span className="list-table__type">{item.document_type}</span>
                          </td>
                          <td className="col-cat">
                            <Badge variant="category" value={item.category} />
                          </td>
                          <td className="col-sum">
                            {item.summary_preview ? (
                              <span className="list-table__summary">{item.summary_preview}</span>
                            ) : (
                              <span className="list-table__muted">분석 전</span>
                            )}
                          </td>
                          <td className="col-status">
                            <Badge variant="status" value={item.status} />
                          </td>
                          <td className="col-date">{formatDateShort(item.created_at)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* ------------------------------------------------- 페이징 */}
              {totalPages > 1 && (
                <nav className="pager" aria-label="페이지 이동">
                  <button
                    type="button"
                    className="btn"
                    disabled={page <= 1}
                    onClick={() => applyParams({ page: page - 1 })}
                  >
                    이전
                  </button>
                  <span className="pager__status">
                    {page} / {totalPages}
                  </span>
                  <button
                    type="button"
                    className="btn"
                    disabled={page >= totalPages}
                    onClick={() => applyParams({ page: page + 1 })}
                  >
                    다음
                  </button>
                </nav>
              )}
            </div>

            {/* ------------------------------------------------ 우: 상세 */}
            {panelOpen && (
              <aside className="list-panel" aria-label="문서 상세">
                <div className="list-panel__bar">
                  <Link to={`/documents/${selectedId}`} className="list-panel__expand">
                    전체 화면으로 보기
                  </Link>
                  <button
                    type="button"
                    className="list-panel__close"
                    onClick={closePanel}
                    aria-label="상세 닫기"
                  >
                    ✕
                  </button>
                </div>

                {detailLoading ? (
                  <Spinner label="상세를 불러오는 중입니다…" />
                ) : detailError ? (
                  <ErrorBanner error={detailError} onRetry={loadDetail} />
                ) : (
                  <>
                    {/* 문서는 그대로 두고 실패 사실만 위에 알린다 */}
                    <ErrorBanner error={actionError} />
                    <DocumentDetail
                      document={detail}
                      onAnalyze={handleAnalyze}
                      onDownload={handleDownload}
                      analyzing={analyzing}
                    />
                  </>
                )}
              </aside>
            )}
          </div>
        )
      )}
    </div>
  )
}
