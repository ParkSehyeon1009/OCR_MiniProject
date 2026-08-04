
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
<<<<<<< HEAD
          <NavLink to="/upload" className={navClass}>
            업로드
          </NavLink>
          <NavLink to="/ocr-compare" className={navClass}>
            OCR 비교
          </NavLink>
=======
>>>>>>> f4a8400b123a6248a64ca22bf912bb424d7d8b74
        </nav>

        {/* --- 인증 삽입 지점 ---
            로그인 도입 시: 비로그인은 <Link to="/login">, 로그인 상태는
            사용자명 + 드롭다운(로그아웃)으로 교체한다. 헤더 밖 코드는 손대지 않는다. */}
        <button
          type="button"
          className="app-user"
          title="로그인"
          aria-label="로그인"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none"
               stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6" />
          </svg>
        </button>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
