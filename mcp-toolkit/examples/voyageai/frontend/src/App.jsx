import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import TripForm from './components/TripForm'
import AgentCard from './components/AgentCard'
import ResultsView from './components/ResultsView'

const ALL_AGENTS = ['weather', 'flights', 'hotels', 'currency']

export default function App() {
  const [screen, setScreen] = useState('form')   // 'form' | 'loading' | 'results'
  const [sessions, setSessions] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [tripForm, setTripForm] = useState(null)  // submitted form data
  const [planData, setPlanData] = useState(null)  // API response

  useEffect(() => { loadSessions() }, [])

  async function loadSessions() {
    try {
      const resp = await fetch('/sessions')
      const data = await resp.json()
      setSessions(data.sessions || [])
    } catch { /* ignore */ }
  }

  function startNewTrip() {
    setSessionId(null)
    setTripForm(null)
    setPlanData(null)
    setScreen('form')
  }

  async function handlePlan(form) {
    setTripForm(form)
    setPlanData(null)
    setScreen('loading')

    try {
      const resp = await fetch('/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, session_id: sessionId || '' }),
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.error || 'Planning failed')

      if (data.session_id) setSessionId(data.session_id)
      setPlanData(data)
      setScreen('results')
      await loadSessions()
    } catch (err) {
      alert(`Error: ${err.message}`)
      setScreen('form')
    }
  }

  // Which agents are expected during loading (based on submitted form)
  const loadingAgents = tripForm
    ? new Set([
        'weather',
        'hotels',
        ...(tripForm.origin?.trim() ? ['flights'] : []),
        ...(tripForm.home_currency ? ['currency'] : []),
      ])
    : new Set()

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={startNewTrip}
        onNewChat={startNewTrip}
      />

      <main className="main-area">
        {screen === 'form' && (
          <TripForm onSubmit={handlePlan} loading={false} />
        )}

        {screen === 'loading' && (
          <div className="loading-page">
            <div className="loading-header">
              <h2>Planning your trip...</h2>
              <p>{loadingAgents.size} agents running in parallel via MCP</p>
            </div>
            <div className="agent-grid">
              {ALL_AGENTS.map(name => (
                <AgentCard
                  key={name}
                  name={name}
                  content={null}
                  isLoading={loadingAgents.has(name)}
                  isSkipped={!loadingAgents.has(name)}
                />
              ))}
            </div>
          </div>
        )}

        {screen === 'results' && planData && (
          <ResultsView
            trip={tripForm}
            data={planData}
            onPlanAnother={startNewTrip}
          />
        )}
      </main>
    </div>
  )
}
