// =============================================================================
// 이 파일의 책임: 카테고리 / 문서 상태 / 추출 방식을 색이 있는 작은 라벨로
//   표시한다. 백엔드가 주는 영문 enum 값(COMPLETED, TEXT_LAYER 등)을 화면에
//   보여줄 한국어 라벨로 바꾸는 매핑도 이 파일이 유일한 출처다.
// 다른 파일과의 관계: pages/ListPage.jsx(표 안), components/DocumentDetail.jsx
//   (상세 헤더)에서 사용한다. 값의 원본은 backend/app/models/enums.py 와
//   backend/app/analyzers/prompts.py 의 CATEGORY_CANDIDATES 다.
// Spring 비교: enum 에 한국어 description 필드를 두고 화면에서 꺼내 쓰는 것과
//   같은 역할. 여기서는 프론트에 매핑 테이블로 둔다.
// =============================================================================

import './Badge.css'

// backend/app/models/enums.py 의 DocumentStatus 와 1:1 대응
const STATUS_MAP = {
  PENDING: { label: '대기', tone: 'neutral' },
  EXTRACTING: { label: '추출 중', tone: 'info' },
  EXTRACTED: { label: '추출 완료', tone: 'info' },
  ANALYZING: { label: '분석 중', tone: 'warning' },
  COMPLETED: { label: '완료', tone: 'success' },
  FAILED: { label: '실패', tone: 'danger' },
}

// backend/app/models/enums.py 의 ExtractMethod 와 1:1 대응
const METHOD_MAP = {
  TEXT_LAYER: { label: '텍스트 레이어', tone: 'neutral' },
  OCR: { label: 'OCR', tone: 'accent' },
  DOCX: { label: 'DOCX', tone: 'neutral' },
  HWPX: { label: 'HWPX', tone: 'neutral' },
  HYBRID: { label: '혼합', tone: 'warning' },
}

// prompts.py 의 CATEGORY_CANDIDATES 와 1:1 대응.
// 한국어를 CSS 클래스명으로 쓸 수 없으므로 영문 키를 따로 둔다.
const CATEGORY_MAP = {
  계약서: 'contract',
  보고서: 'report',
  회의록: 'minutes',
  공지사항: 'notice',
  메뉴얼: 'manual',
  기타: 'etc',
}

export default function Badge({ variant, value }) {
  // 값이 없으면 아무것도 그리지 않는다 (분석 전 문서는 category 가 null).
  if (!value) return <span className="badge badge--empty">—</span>

  if (variant === 'category') {
    const key = CATEGORY_MAP[value] || 'etc'
    return <span className={`badge badge-cat badge-cat--${key}`}>{value}</span>
  }

  const map = variant === 'status' ? STATUS_MAP : METHOD_MAP
  // 매핑에 없는 값이 와도 화면이 깨지지 않게 원본 값을 그대로 보여준다.
  const entry = map[value] || { label: value, tone: 'neutral' }

  return <span className={`badge badge--${entry.tone}`}>{entry.label}</span>
}
