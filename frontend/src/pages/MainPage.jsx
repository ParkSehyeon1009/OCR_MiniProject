import { useState } from 'react'
import './MainPage.css'

const MENU_ITEMS = [
  {
    key: '문서업로드',
    label: '문서업로드',
    description: [
      'PDF · DOCX · HWPX · 이미지 파일을 최대 10MB까지 올릴 수 있습니다.',
      '파일을 끌어다 놓거나 직접 선택해 전송하세요.',
      '문서에 글자 정보가 있으면 그대로 읽고, 없으면 OCR로 인식합니다.',
      '표나 직인처럼 이미지로 된 부분은 자동으로 OCR을 함께 사용합니다.',
      '업로드가 끝나면 원본과 추출된 텍스트를 나란히 비교할 수 있습니다.',
    ]
  },
  {
    key: 'AI분석',
    label: 'AI분석',
    description: [
      '추출된 내용을 바탕으로 문서를 3~5문장으로 요약하고, 계약서 · 보고서 · 회의록 · 공지사항 · 메뉴얼 · 기타 여섯 가지 중 하나로 분류합니다.',
      '분류를 선택한 이유도 함께 제시하므로 결과가 타당한지 검토할 수 있습니다.',
      '요약과 분류는 필요한 것만 골라 실행할 수 있습니다.',
    ]
  },
  {
    key: '검색 · 다운로드',
    label: '검색 · 다운로드',
    description: [
      '파일명뿐 아니라 문서 본문 내용으로도 검색할 수 있고, 카테고리로 걸러 볼 수 있습니다.',
      '목록에서 문서를 선택하면 오른쪽에 요약 · 분류 근거 · 원문 · 분석 이력이 표시됩니다.',
      '요약 결과는 텍스트 파일로 내려받아 보관할 수 있습니다.',
    ]
  },
]

const DEFAULT_TITLE = '서비스 소개'
const DEFAULT_DESCRIPTION =
  [
    'PDF Brief AI /n문서를 올리면 내용을 자동으로 읽어 요약하고, 종류별로 분류해 주는 서비스입니다.',
    '스캔 문서나 이미지도 OCR로 글자를 인식하므로, 검색이 되지 않던 자료까지 한곳에서 찾아볼 수 있습니다.',
    '왼쪽 메뉴에 마우스를 올리면 각 기능의 사용 방법을 볼 수 있습니다.'
  ]

function MainPage() {
  const [activeKey, setActiveKey] = useState(null)
  const active = MENU_ITEMS.find((item) => item.key === activeKey)

  return (
    <div className="main-page">

      <div className="main-body">
        <nav className="side-menu" onMouseLeave={() => setActiveKey(null)}>
          {MENU_ITEMS.map((item) => (
            <div
              key={item.key}
              className={`menu-item${activeKey === item.key ? ' active' : ''}`}
              onMouseEnter={() => setActiveKey(item.key)}
            >
              {item.label}
            </div>
          ))}
        </nav>

        <section className="content-area">
          <h2>{active ? active.label : DEFAULT_TITLE}</h2>
          {(active ? active.description : DEFAULT_DESCRIPTION).map((text) => (
          <p key={text}>{text}</p>
          ))}
        </section>
      </div>
    </div>
  )
}

export default MainPage
