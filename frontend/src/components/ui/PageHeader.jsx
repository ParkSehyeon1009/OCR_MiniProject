import './PageHeader.css'

export default function PageHeader({ eyebrow, title, description, actions, meta }) {
  return (
    <header className="page-header">
      <div className="page-header__copy">
        {eyebrow && <p className="page-header__eyebrow">{eyebrow}</p>}
        <div className="page-header__title-row">
          <h1>{title}</h1>
          {meta && <div className="page-header__meta">{meta}</div>}
        </div>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </header>
  )
}
