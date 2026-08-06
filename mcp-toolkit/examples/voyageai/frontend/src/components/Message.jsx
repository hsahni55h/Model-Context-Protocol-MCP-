/**
 * Renders a single chat bubble.
 *
 * The `isWelcome` flag renders the hard-coded intro message with JSX markup
 * instead of plain text — avoids dangerouslySetInnerHTML for the list items.
 */
export default function Message({ role, content, isWelcome }) {
  if (isWelcome) {
    return (
      <div className="message assistant">
        <div className="message-content">
          Hi! I&apos;m VoyageAI, your travel planning assistant. I can help you with:
          <ul>
            <li>Finding flights between cities</li>
            <li>Checking weather at your destination</li>
            <li>Searching for hotels and attractions</li>
            <li>Converting currencies for your budget</li>
          </ul>
          Where would you like to go?
        </div>
      </div>
    )
  }

  return (
    <div className={`message ${role}`}>
      <div className="message-content">{content}</div>
    </div>
  )
}
