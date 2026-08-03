const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const sessionList = document.getElementById('session-list');
const newChatBtn = document.getElementById('new-chat-btn');

let sessionId = null;

// Welcome message HTML (reused when starting new chats)
const WELCOME_HTML = `
    <div class="message assistant">
        <div class="message-content">
            Hi! I'm VoyageAI, your travel planning assistant. I can help you with:
            <ul>
                <li>Finding flights between cities</li>
                <li>Checking weather at your destination</li>
                <li>Searching for hotels and attractions</li>
                <li>Converting currencies for your budget</li>
            </ul>
            Where would you like to go?
        </div>
    </div>`;

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addLoading() {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'loading-msg';
    div.innerHTML = '<div class="message-content"><span class="loading"></span> Thinking...</div>';
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeLoading() {
    const el = document.getElementById('loading-msg');
    if (el) el.remove();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    addMessage('user', message);
    userInput.value = '';
    sendBtn.disabled = true;
    addLoading();

    try {
        const resp = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId }),
        });
        const data = await resp.json();

        removeLoading();
        addMessage('assistant', data.response);

        // Track session ID from server
        if (data.session_id) {
            sessionId = data.session_id;
        }

        // Refresh sidebar
        await loadSessions();
    } catch (err) {
        removeLoading();
        addMessage('assistant', 'Sorry, something went wrong. Please try again.');
    }

    sendBtn.disabled = false;
    userInput.focus();
}

function startNewChat() {
    sessionId = null;
    chatContainer.innerHTML = WELCOME_HTML;
    // Remove active state from sidebar
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    userInput.focus();
}

async function loadSession(id) {
    sessionId = id;
    try {
        const resp = await fetch(`/sessions/${id}`);
        const data = await resp.json();

        chatContainer.innerHTML = WELCOME_HTML;
        for (const msg of data.history) {
            addMessage(msg.role, msg.content);
        }

        // Highlight active session
        document.querySelectorAll('.session-item').forEach(el => {
            el.classList.toggle('active', el.dataset.id === id);
        });
    } catch (err) {
        console.error('Failed to load session:', err);
    }
}

async function loadSessions() {
    try {
        const resp = await fetch('/sessions');
        const data = await resp.json();

        sessionList.innerHTML = '';
        for (const session of data.sessions) {
            const div = document.createElement('div');
            div.className = `session-item${session.id === sessionId ? ' active' : ''}`;
            div.dataset.id = session.id;
            div.textContent = session.title || 'New conversation';
            div.onclick = () => loadSession(session.id);
            sessionList.appendChild(div);
        }
    } catch (err) {
        console.error('Failed to load sessions:', err);
    }
}

// Event listeners
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

newChatBtn.addEventListener('click', startNewChat);

// Load existing sessions on page load
loadSessions();
