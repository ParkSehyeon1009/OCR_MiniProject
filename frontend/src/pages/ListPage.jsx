// =============================================================================
// 이 파일의 책임: 문서 목록 화면. 검색어·카테고리·페이지 조건으로
//   GET /api/documents 를 호출해 표로 보여준다. 조회 조건을 컴포넌트 state 가
//   아니라 URL 쿼리스트링에 보관하여, 새로고침·뒤로가기·주소 공유 시에도
//   같은 결과가 재현되게 한다.
// 다른 파일과의 관계: api/documents.js 의 fetchDocuments() 를 호출하고,
//   components/Badge·Spinner·ErrorBanner 와 utils/format.js 를 사용한다.
//   행의 파일명을 누르면 /documents/:id (DetailPage) 로 이동한다.
//   쿼리 파라미터 이름은 backend/app/api/routes/document_router.py 의
//   list_documents() 시그니처와 1:1로 맞춘다.
// Spring 비교: Controller 가 @RequestParam 을 받아 Service 를 호출하고 Model 에
//   담아 뷰로 넘기는 흐름을, 이 컴포넌트가 useSearchParams + useEffect 로
//   대신한다. 응답은 Spring Data 의 Page<T> 와 같은 구조다.
// =============================================================================

import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import Badge from '../components/Badge'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import { listDocuments } from '../api/document'
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

  // 입력 중인 검색어만 로컬 state 로 둔다 (제출 시 URL 로 승격).
  const [keyword, setKeyword] = useState(q)

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // 재시도 버튼이 같은 조건으로 다시 호출하도록 만드는 트리거
  const [reloadKey, setReloadKey] = useState(0)

  // 뒤로가기 등으로 URL 이 바뀌면 입력창도 따라가게 한다.
  useEffect(() => {
    setKeyword(q)
  }, [q])

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

  /** 조회 조건을 URL 에 반영한다. 빈 값은 파라미터에서 제거해 주소를 깔끔히 유지한다. */
  function applyParams(next) {
    const merged = { q, category, page: 1, ...next }
    const params = {}

    if (merged.q) params.q = merged.q
    if (merged.category) params.category = merged.category
    if (merged.page > 1) params.page = String(merged.page)

    setSearchParams(params)
  }

  function handleSubmit(event) {
    event.preventDefault() // 폼 기본 동작(새로고침)을 막는다
    applyParams({ q: keyword.trim() })
  }

  function handleReset() {
    setKeyword('')
    setSearchParams({})
  }

  const items = data?.items || []
  const totalPages = data?.total_pages || 0
  const hasFilter = Boolean(q || category)

  return (
    <div className="c-scope list-page">
      <header className="list-page__head">
        <h1 className="list-page__title">문서 목록</h1>
        {data && (
          <p className="list-page__total">
            전체 <strong>{data.total}</strong>건
            {hasFilter && ' (검색 결과)'}
          </p>
        )}
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

      {/* --------------------------------------------------------- 본문 */}
      <ErrorBanner error={error} onRetry={() => setReloadKey((n) => n + 1)} />

      {loading ? (
        <Spinner label="문서를 불러오는 중입니다…" />
      ) : (
        !error && (
          <>
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
                      <tr key={item.id}>
                        <td className="col-name">
                          {/* 링크로 두어 키보드 이동과 새 탭 열기가 되게 한다 */}
                          <Link to={`/documents/${item.id}`} className="list-table__link">
                            {item.filename}
                          </Link>
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
          </>
        )
      )}
    </div>
  )
}
