import { useState } from 'react'
import './App.css'
import MainPage from './pages/MainPage'
import TestPage from './pages/TestPage'

function App() {
  const [view, setView] = useState('main')

  return (
    <>
      <div className="view-switch">
        <button type="button" onClick={() => setView('main')} disabled={view === 'main'}>
          메인 페이지
        </button>
        <button type="button" onClick={() => setView('test')} disabled={view === 'test'}>
          API 테스트
        </button>
      </div>
      {view === 'main' ? <MainPage /> : <TestPage />}
    </>
  )
}

export default App
