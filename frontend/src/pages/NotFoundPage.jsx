import { Link } from 'react-router-dom'
import EmptyState from '../components/ui/EmptyState'
import './NotFoundPage.css'

export default function NotFoundPage() {
  return (
    <main className="c-scope not-found-page">
      <EmptyState
        icon="documents"
        title="페이지를 찾을 수 없습니다"
        description="주소가 변경되었거나 존재하지 않는 페이지입니다. 홈에서 다시 시작해 주세요."
        action={<Link className="btn btn--primary" to="/">홈으로 이동</Link>}
      />
    </main>
  )
}
