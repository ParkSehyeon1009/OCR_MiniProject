import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import MainPage from './pages/MainPage'
import ListPage from './pages/ListPage'
import DetailPage from './pages/DetailPage'
import TestPage from './pages/TestPage'
import OcrComparePage from './pages/OcrComparePage'
import NotFoundPage from './pages/NotFoundPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<MainPage />} />
          <Route path="/documents" element={<ListPage />} />
          <Route path="/documents/:id" element={<DetailPage />} />
          <Route path="/upload" element={<TestPage />} />
          <Route path="/ocr-compare" element={<OcrComparePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
