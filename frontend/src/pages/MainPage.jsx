import { Link } from 'react-router-dom'
import Icon from '../components/ui/Icon'
import './MainPage.css'

const WORKFLOWS = [
  {
    step: '01',
    icon: 'upload',
    title: '문서 업로드',
    description: 'PDF, DOCX, HWPX, 이미지 파일을 올리면 텍스트 레이어와 OCR을 자동으로 선택합니다.',
  },
  {
    step: '02',
    icon: 'compare',
    title: '원본과 추출 결과 확인',
    description: '원본 문서와 추출 텍스트를 나란히 보면서 인식 결과를 빠르게 검토할 수 있습니다.',
  },
  {
    step: '03',
    icon: 'sparkles',
    title: '요약 및 분류',
    description: '필요한 분석만 선택해 핵심 요약, 문서 유형, 분류 근거를 생성합니다.',
  },
]

const FEATURES = [
  { icon: 'search', title: '본문까지 통합 검색', text: '파일명과 추출된 원문을 함께 검색합니다.' },
  { icon: 'documents', title: '한곳에서 문서 관리', text: '요약, 분류, 원문, 분석 이력을 한 화면에서 확인합니다.' },
  { icon: 'shield', title: '보수적인 자동 처리', text: '문서 상태에 맞는 추출 방식을 선택하고 실패 원인을 안내합니다.' },
]

export default function MainPage() {
  return (
    <div className="c-scope main-page">
      <section className="home-hero">
        <div className="home-hero__copy">
          <p className="home-hero__eyebrow">DOCUMENT INTELLIGENCE WORKSPACE</p>
          <h1>읽기 어려운 문서를<br /><span>검색 가능한 지식</span>으로.</h1>
          <p className="home-hero__description">
            문서를 업로드하면 텍스트를 추출하고, 필요한 경우 OCR을 적용합니다.
            결과를 직접 비교한 뒤 요약과 분류까지 하나의 흐름에서 진행하세요.
          </p>
          <div className="home-hero__actions">
            <Link to="/upload" className="btn btn--primary home-hero__primary">
              문서 업로드 <Icon name="arrowRight" size={17} />
            </Link>
            <Link to="/documents" className="btn">문서 목록 보기</Link>
          </div>
          <ul className="home-hero__trust" aria-label="지원 기능">
            <li><Icon name="check" size={15} /> PDF · DOCX · HWPX · 이미지</li>
            <li><Icon name="check" size={15} /> 최대 10MB · PDF 30페이지</li>
            <li><Icon name="check" size={15} /> OCR · 요약 · 분류</li>
          </ul>
        </div>

        <div className="home-hero__visual" aria-hidden="true">
          <div className="hero-document hero-document--back">
            <span /><span /><span /><span />
          </div>
          <div className="hero-document hero-document--front">
            <div className="hero-document__top"><Icon name="documents" size={19} /><b>문서 분석 결과</b></div>
            <span className="hero-document__title" />
            <span /><span /><span />
            <div className="hero-document__summary">
              <Icon name="sparkles" size={16} />
              <div><i /><i /><i /></div>
            </div>
          </div>
          <div className="hero-float hero-float--ocr">OCR 완료</div>
          <div className="hero-float hero-float--category">보고서</div>
        </div>
      </section>

      <section className="home-section" aria-labelledby="workflow-title">
        <div className="home-section__head">
          <p>HOW IT WORKS</p>
          <h2 id="workflow-title">문서 처리 과정을 한눈에</h2>
        </div>
        <div className="workflow-grid">
          {WORKFLOWS.map((item) => (
            <article className="workflow-card" key={item.step}>
              <div className="workflow-card__top">
                <span className="workflow-card__icon"><Icon name={item.icon} size={21} /></span>
                <span className="workflow-card__step">{item.step}</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="home-feature-band">
        {FEATURES.map((item) => (
          <div className="home-feature" key={item.title}>
            <Icon name={item.icon} size={21} />
            <div><strong>{item.title}</strong><p>{item.text}</p></div>
          </div>
        ))}
      </section>
    </div>
  )
}
