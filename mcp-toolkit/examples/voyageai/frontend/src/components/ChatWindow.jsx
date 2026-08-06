import { useState, useEffect, useRef } from 'react'
import Message from './Message'

export default function ChatWindow({ messages, loading, onSendMessage }) {
  const [input, setInput] = useState('')
  const chatEndRef = useRef(null)

  // Auto-scroll to the bottom whenever messages or loading state changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function handleSubmit(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return
    onSendMessage(text)
    setInput('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>✈️ VoyageAI</h1>
        <p className="subtitle">AI-powered travel planner using MCP</p>
      </header>

      <div className="chat-container">
        {messages.map((msg, i) => (
          <Message
            key={i}
            role={msg.role}
            content={msg.content}
            isWelcome={msg.isWelcome}
          />
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <span className="loading" /> Thinking...
            </div>
          </div>
        )}

        {/* Invisible sentinel element — scroll target */}
        <div ref={chatEndRef} />
      </div>

      <form className="input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          className="user-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Plan a trip to Tokyo next week..."
          disabled={loading}
          autoFocus
        />
        <button type="submit" className="send-btn" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  )
}
