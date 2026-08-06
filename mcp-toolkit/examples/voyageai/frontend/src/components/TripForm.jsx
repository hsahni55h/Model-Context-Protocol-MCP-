import { useState } from 'react'

const CURRENCIES = [
  'GBP', 'USD', 'EUR', 'AUD', 'CAD', 'JPY', 'INR',
  'CHF', 'SEK', 'NOK', 'DKK', 'SGD', 'HKD', 'CNY',
]

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    origin: '',
    destination: '',
    departure_date: '',
    return_date: '',
    home_currency: 'GBP',
  })
  const [errors, setErrors] = useState({})

  function update(field, value) {
    setForm(prev => ({ ...prev, [field]: value }))
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: '' }))
  }

  function validate() {
    const errs = {}
    if (!form.destination.trim()) errs.destination = 'Please enter a destination'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!loading && validate()) onSubmit(form)
  }

  const agentsWillRun = ['weather', 'hotels']
  if (form.origin.trim()) agentsWillRun.push('flights')
  if (form.home_currency) agentsWillRun.push('currency')

  const agentsMeta = {
    weather:  { emoji: '🌤', label: 'Weather' },
    flights:  { emoji: '✈️', label: 'Flights' },
    hotels:   { emoji: '🏨', label: 'Hotels' },
    currency: { emoji: '💱', label: 'Currency' },
  }
  const agentsSkipped = ['flights', 'currency'].filter(a => !agentsWillRun.includes(a))

  return (
    <div className="form-page">
      <div className="form-branding">
        <div className="form-logo">✈️</div>
        <h1>VoyageAI</h1>
        <p>Multi-agent AI travel planner · Powered by MCP</p>
      </div>

      <form className="trip-form" onSubmit={handleSubmit}>
        <div className="form-row two-col">
          <div className="form-field">
            <label>
              Flying from
              <span className="badge-optional">optional</span>
            </label>
            <input
              type="text"
              placeholder="e.g. London"
              value={form.origin}
              onChange={e => update('origin', e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="form-field">
            <label>
              Destination
              <span className="badge-required">required</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Stockholm"
              value={form.destination}
              onChange={e => update('destination', e.target.value)}
              className={errors.destination ? 'input-error' : ''}
              disabled={loading}
            />
            {errors.destination && <p className="field-error">{errors.destination}</p>}
          </div>
        </div>

        <div className="form-row two-col">
          <div className="form-field">
            <label>Departure date</label>
            <input
              type="date"
              value={form.departure_date}
              onChange={e => update('departure_date', e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="form-field">
            <label>
              Return date
              <span className="badge-optional">optional</span>
            </label>
            <input
              type="date"
              value={form.return_date}
              min={form.departure_date || undefined}
              onChange={e => update('return_date', e.target.value)}
              disabled={loading}
            />
          </div>
        </div>

        <div className="form-row single-col">
          <div className="form-field">
            <label>
              Home currency
              <span className="badge-optional">optional — for exchange rates</span>
            </label>
            <select
              value={form.home_currency}
              onChange={e => update('home_currency', e.target.value)}
              disabled={loading}
            >
              <option value="">Skip currency conversion</option>
              {CURRENCIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="agents-hint">
          <span className="hint-label">Agents that will run:</span>
          {agentsWillRun.map(a => (
            <span key={a} className="hint-agent will-run">
              {agentsMeta[a].emoji} {agentsMeta[a].label}
            </span>
          ))}
          {agentsSkipped.map(a => (
            <span key={a} className="hint-agent wont-run">
              {agentsMeta[a].emoji} {agentsMeta[a].label}
            </span>
          ))}
        </div>

        <button type="submit" className="plan-btn" disabled={loading}>
          {loading
            ? <><span className="btn-spinner" /> Planning your trip...</>
            : 'Plan My Trip →'
          }
        </button>
      </form>
    </div>
  )
}
