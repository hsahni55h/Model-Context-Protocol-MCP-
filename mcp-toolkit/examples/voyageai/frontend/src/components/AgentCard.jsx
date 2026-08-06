import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const META = {
  weather:  { emoji: '🌤', label: 'Weather Forecast' },
  flights:  { emoji: '✈️', label: 'Flight Options' },
  hotels:   { emoji: '🏨', label: 'Hotels & Attractions' },
  currency: { emoji: '💱', label: 'Currency & Rates' },
}

export default function AgentCard({ name, content, isLoading, isSkipped }) {
  const { emoji, label } = META[name] || { emoji: '🔧', label: name }

  let statusBadge = null
  if (isLoading) statusBadge = <span className="agent-spinner" />
  else if (isSkipped) statusBadge = <span className="badge-skipped">not requested</span>
  else if (content) statusBadge = <span className="badge-done">✓</span>

  return (
    <div className={`agent-card${isSkipped ? ' agent-card--skipped' : ''}`}>
      <div className="agent-card-header">
        <span className="agent-emoji">{emoji}</span>
        <span className="agent-label">{label}</span>
        {statusBadge}
      </div>
      <div className="agent-card-body">
        {isLoading && (
          <div className="skeleton">
            <div className="skeleton-line" style={{ width: '88%' }} />
            <div className="skeleton-line" style={{ width: '65%' }} />
            <div className="skeleton-line" style={{ width: '82%' }} />
            <div className="skeleton-line" style={{ width: '50%' }} />
            <div className="skeleton-line" style={{ width: '75%' }} />
          </div>
        )}
        {isSkipped && (
          <p className="skipped-msg">Not requested for this trip.</p>
        )}
        {!isLoading && !isSkipped && content && (
          <div className="card-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
