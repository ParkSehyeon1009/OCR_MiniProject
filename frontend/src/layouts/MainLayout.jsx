// =============================================================================
// 이 파일의 책임: 모든 화면이 공유하는 상단 헤더와 네비게이션을 그리고,
//   그 아래에 현재 라우트의 페이지를 끼워 넣는다(Outlet).
// 다른 파일과의 관계: App.jsx 가 라우트 트리의 최상위 element 로 사용한다.
//   자식 페이지는 MainPage / ListPage / DetailPage / TestPage 다.
//   주의: 여기에 .c-scope 를 붙이지 않는다. 붙이면 기존 MainPage·TestPage 의
//   글자 크기와 정렬까지 바뀌므로, .c-scope 는 각 페이지가 스스로 적용한다.
// Spring 비교: Thymeleaf 의 레이아웃 템플릿(공통 header + 본문 fragment 삽입)
//   과 같은 역할. Outlet 이 th:insert 로 끼워지는 자리에 해당한다.
// =============================================================================

import { NavLink, Outlet } from 'react-router-dom'
import './MainLayout.css'

// isActive 를 받아 현재 메뉴를 강조한다 (react-router 가 넘겨준다).
function navClass({ isActive }) {
  return isActive ? 'main-nav__link main-nav__link--active' : 'main-nav__link'
}

export default function MainLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="app-brand">
          PDF Brief <span>AI</span>
        </NavLink>

        <nav className="main-nav">
          {/* end: "/" 는 정확히 일치할 때만 활성화 (없으면 항상 활성 상태가 된다) */}
          <NavLink to="/" className={navClass} end>
            홈
          </NavLink>
          <NavLink to="/documents" className={navClass}>
            문서 목록
          </NavLink>
          <NavLink to="/upload" className={navClass}>
            업로드
          </NavLink>
          <NavLink to="/ocr-compare" className={navClass}>
            OCR 비교
          </NavLink>
        </nav>

        {/* 로그인 기능을 넣게 되면 이 자리에 사용자 메뉴가 들어간다.
            <div className="app-header__user"> ... </div> */}
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
