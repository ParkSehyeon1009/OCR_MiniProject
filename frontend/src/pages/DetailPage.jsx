// =============================================================================
// 이 파일의 책임: 문서 상세 화면의 데이터 담당. URL 의 :id 로 상세를 조회하고,
//   분석 실행·다운로드 동작을 수행한 뒤 결과를 DocumentDetail 에 넘긴다.
//   화면 표현은 전혀 하지 않는다 (표현은 components/DocumentDetail.jsx).
// 다른 파일과의 관계: api/documents.js 의 getDocument / analyzeDocument /
//   downloadSummary 를 호출한다. 조회 실패는 화면 전체를 대체하는 에러로,
//   분석·다운로드 실패는 문서 내용을 유지한 채 보여주는 에러로 구분해 다룬다.
// Spring 비교: 조회용 Controller 메서드에 해당. 데이터를 모아 뷰(DocumentDetail)
//   에 넘기는 역할만 하고, 화면 조립은 뷰가 담당하는 구조다.
// =============================================================================

import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import DocumentDetail from '../components/DocumentDetail'
import Spinner from '../components/Spinner'
import ErrorBanner from '../components/ErrorBanner'
import { getDocument, analyzeDocument, downloadSummary } from '../api/document'
import './DetailPage.css'

export default function DetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const [document, setDocument] = useState(null)
  const [loading, setLoading] = useState(true)
  // 문서 조회 자체가 실패한 경우 (화면에 보여줄 내용이 없음)
  const [loadError, setLoadError] = useState(null)
  // 분석·다운로드처럼 이미 뜬 문서 위에서 실패한 경우 (문서는 계속 보여준다)
  const [actionError, setActionError] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      setDocument(await getDocument(id))
    } catch (err) {
      setLoadError(err)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  async function handleAnalyze() {
    setAnalyzing(true)
    setActionError(null)
    try {
      await analyzeDocument(id)
      // 분석 결과뿐 아니라 status 도 바뀌므로 상세를 다시 조회한다.
      setDocument(await getDocument(id))
    } catch (err) {
      setActionError(err)
    } finally {
      setAnalyzing(false)
    }
  }

  async function handleDownload() {
    setActionError(null)
    try {
      // 파일 저장은 api/documents.js 가 처리한다. 실패 시에만 여기서 다룬다.
      await downloadSummary(id, `${document.filename}_요약.txt`)
    } catch (err) {
      setActionError(err)
    }
  }

  /**
   * 목록으로 돌아갈 때, 직전 화면이 목록이면 뒤로가기로 처리해 검색 조건과
   * 페이지 번호를 그대로 유지한다. 상세 URL 로 바로 들어온 경우엔 히스토리가
   * 없으므로 목록 주소로 이동한다.
   */
  function handleBack() {
    if (location.key === 'default') {
      navigate('/documents')
    } else {
      navigate(-1)
    }
  }

  return (
    <div className="c-scope detail-page">
      <nav className="detail-page__nav">
        <button type="button" className="detail-page__back" onClick={handleBack}>
          ← 목록으로
        </button>
      </nav>

      {loading ? (
        <Spinner label="문서를 불러오는 중입니다…" />
      ) : loadError ? (
        <>
          <ErrorBanner error={loadError} onRetry={load} />
          <p className="detail-page__fallback">
            <Link to="/documents">문서 목록으로 이동</Link>
          </p>
        </>
      ) : (
        <>
          {/* 문서는 그대로 두고 실패 사실만 위에 알린다 */}
          <ErrorBanner error={actionError} />
          <DocumentDetail
            document={document}
            onAnalyze={handleAnalyze}
            onDownload={handleDownload}
            analyzing={analyzing}
          />
        </>
      )}
    </div>
  )
}
