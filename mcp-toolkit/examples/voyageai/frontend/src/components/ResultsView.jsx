import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import AgentCard from './AgentCard'

const ALL_AGENTS = ['weather', 'flights', 'hotels', 'currency']

export default function ResultsView({ trip, data, onPlanAnother }) {
  const { agents_called = [], results = {}, summary = '' } = data
  const calledSet = new Set(agents_called)

  const parts = []
  if (trip.origin && trip.destination) {
    parts.push(`${trip.origin} → ${trip.destination}`)
  } else if (trip.destination) {
    parts.push(trip.destination)
  }
  if (trip.departure_date) parts.push(trip.departure_date)
  if (trip.return_date) parts.push(`↩ ${trip.return_date}`)

  return (
    <div className="results-page">
      <div className="results-header">
        <div>
          <h2 className="results-title">✈️ {parts.join('  ·  ')}</h2>
          <p className="results-meta">
            {agents_called.length} agents ran in parallel via MCP
          </p>
        </div>
        <button className="new-plan-btn" onClick={onPlanAnother}>
          + New Trip
        </button>
      </div>

      <div className="agent-grid">
        {ALL_AGENTS.map(name => (
          <AgentCard
            key={name}
            name={name}
            content={results[name] || null}
            isLoading={false}
            isSkipped={!calledSet.has(name)}
          />
        ))}
      </div>

      {summary && (
        <div className="summary-card">
          <div className="summary-header">
            <span>📋</span>
            <h3>Trip Itinerary</h3>
          </div>
          <div className="card-markdown summary-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}
