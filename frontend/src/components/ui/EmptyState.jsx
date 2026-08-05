import { Link } from 'react-router-dom'
import Icon from './Icon'
import './EmptyState.css'

export default function EmptyState({ icon = 'documents', title, description, action }) {
  return (
    <div className="empty-state">
      <span className="empty-state__icon"><Icon name={icon} size={23} /></span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action && (
        action.to ? (
          <Link to={action.to} className="btn btn--primary">{action.label}</Link>
        ) : (
          <button type="button" className="btn btn--primary" onClick={action.onClick}>
            {action.label}
          </button>
        )
      )}
    </div>
  )
}
