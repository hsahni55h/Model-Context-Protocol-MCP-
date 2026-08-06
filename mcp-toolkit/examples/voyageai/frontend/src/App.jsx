import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'

// Sentinel object for the static welcome message shown at the top of every session
const WELCOME_MESSAGE = { role: 'assistant', content: null, isWelcome: true }

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [sessions, setSessions] = useState([])
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [loading, setLoading] = useState(false)

  // Load sidebar sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  async function loadSessions() {
    try {
      const resp = await fetch('/sessions')
      const data = await resp.json()
      setSessions(data.sessions || [])
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  async function loadSession(id) {
    setSessionId(id)
    try {
      const resp = await fetch(`/sessions/${id}`)
      if (!resp.ok) return
      const data = await resp.json()
      setMessages([WELCOME_MESSAGE, ...data.history])
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }

  function startNewChat() {
    setSessionId(null)
    setMessages([WELCOME_MESSAGE])
  }

  async function sendMessage(text) {
    if (!text.trim() || loading) return

    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const resp = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId || '' }),
      })
      const data = await resp.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])

      if (data.session_id) {
        setSessionId(data.session_id)
      }
      await loadSessions()
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        currentSessionId={sessionId}
        onSelectSession={loadSession}
        onNewChat={startNewChat}
      />
      <ChatWindow
        messages={messages}
        loading={loading}
        onSendMessage={sendMessage}
      />
    </div>
  )
}
