import { NavLink, Outlet } from 'react-router-dom'
import Icon from '../components/ui/Icon'
import './MainLayout.css'

const NAV_ITEMS = [
  { to: '/', label: '홈', icon: 'home', end: true },
  { to: '/documents', label: '문서', icon: 'documents' },
  { to: '/upload', label: '업로드', icon: 'upload' },
  { to: '/ocr-compare', label: 'OCR 비교', icon: 'compare' },
]

function navClass({ isActive }) {
  return isActive ? 'main-nav__link main-nav__link--active' : 'main-nav__link'
}

export default function MainLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__inner">
          <NavLink to="/" className="app-brand" aria-label="PDF Brief AI 홈">
            <span className="app-brand__mark"><Icon name="sparkles" size={18} /></span>
            <span className="app-brand__text">PDF Brief <strong>AI</strong></span>
          </NavLink>

          <nav className="main-nav" aria-label="주요 메뉴">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={navClass}
              >
                <Icon name={item.icon} size={17} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          <button type="button" className="app-user" title="로그인 준비 중" aria-label="사용자 메뉴">
            <Icon name="user" size={18} />
          </button>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
