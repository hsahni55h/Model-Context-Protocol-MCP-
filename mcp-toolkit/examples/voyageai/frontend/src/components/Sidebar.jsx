export default function Sidebar({ sessions, currentSessionId, onSelectSession, onNewChat }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Conversations</h2>
        <button className="new-chat-btn" onClick={onNewChat} title="New conversation">
          +
        </button>
      </div>
      <div className="session-list">
        {sessions.map(session => (
          <div
            key={session.id}
            className={`session-item${session.id === currentSessionId ? ' active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            {session.title || 'New conversation'}
          </div>
        ))}
      </div>
    </aside>
  )
}
