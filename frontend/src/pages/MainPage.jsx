import { useState } from 'react'
import './MainPage.css'

const MENU_ITEMS = [
  {
    key: 'A',
    label: 'A',
    description: 'A 기능 더미 설명입니다. 실제 기능이 확정되면 이 영역에 A 기능 소개와 사용법이 표시됩니다.',
  },
  {
    key: 'B',
    label: 'B',
    description: 'B 기능 더미 설명입니다. 실제 기능이 확정되면 이 영역에 B 기능 소개와 사용법이 표시됩니다.',
  },
  {
    key: 'C',
    label: 'C',
    description: 'C 기능 더미 설명입니다. 실제 기능이 확정되면 이 영역에 C 기능 소개와 사용법이 표시됩니다.',
  },
]

const DEFAULT_TITLE = '서비스 소개'
const DEFAULT_DESCRIPTION =
  '전체적인 웹 서비스 요약과 기능, 대략적인 사용 방법이 기본으로 표시되는 영역입니다. 왼쪽 메뉴에 마우스를 올리면 해당 기능 설명으로 바뀝니다.'

function MainPage() {
  const [activeKey, setActiveKey] = useState(null)
  const active = MENU_ITEMS.find((item) => item.key === activeKey)

  return (
    <div className="main-page">
      <header className="main-header">
        <span className="project-name">Project Name</span>
        <div className="user-icon" title="사용자 로그인">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6" />
          </svg>
        </div>
      </header>

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
          <p>{active ? active.description : DEFAULT_DESCRIPTION}</p>
        </section>
      </div>
    </div>
  )
}

export default MainPage
