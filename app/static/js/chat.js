/**
 * EduPilot – AI Chat JavaScript
 * Handles chat interface, message sending, and rendering
 */

// Render markdown in existing assistant messages
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.chat-content').forEach(el => {
    el.innerHTML = marked.parse(el.textContent || '');
  });
  scrollToBottom();
});

function scrollToBottom() {
  const msgs = document.getElementById('chatMessages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function handleEnter(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function sendSuggestion(btn) {
  const text = btn.textContent.replace(/^[^\s]+\s/, ''); // Remove emoji
  document.getElementById('chatInput').value = btn.textContent;
  sendMessage();

  // Hide suggestions after first use
  const suggestionsEl = document.getElementById('chatSuggestions');
  if (suggestionsEl) {
    suggestionsEl.style.opacity = '0';
    suggestionsEl.style.transition = 'opacity 0.3s ease';
    setTimeout(() => { suggestionsEl.style.display = 'none'; }, 300);
  }
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const message = input.value.trim();

  if (!message) return;

  // Disable input while sending
  input.value = '';
  input.style.height = 'auto';
  input.disabled = true;
  sendBtn.disabled = true;
  sendBtn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px;"></div>';

  // Remove welcome message
  const welcomeMsg = document.getElementById('welcomeMsg');
  if (welcomeMsg) welcomeMsg.remove();

  // Add user bubble
  addBubble(message, 'user');

  // Show typing indicator
  const typingIndicator = document.getElementById('typingIndicator');
  if (typingIndicator) typingIndicator.style.display = 'block';
  scrollToBottom();

  try {
    const resp = await fetch('/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    const data = await resp.json();

    // Hide typing
    if (typingIndicator) typingIndicator.style.display = 'none';

    if (data.response) {
      addBubble(data.response, 'assistant', true);
    } else if (data.error) {
      addBubble(`⚠️ Error: ${data.error}`, 'assistant');
    }

  } catch (err) {
    if (typingIndicator) typingIndicator.style.display = 'none';
    addBubble('⚠️ Connection error. Please check your internet connection and try again.', 'assistant');
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    sendBtn.innerHTML = '<i class="bi bi-send-fill"></i>';
    input.focus();
    scrollToBottom();
  }
}

function addBubble(content, role, renderMarkdown = false) {
  const container = document.getElementById('chatMessages');
  const typingIndicator = document.getElementById('typingIndicator');

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  bubble.style.opacity = '0';
  bubble.style.transform = 'translateY(10px)';

  if (renderMarkdown && role === 'assistant') {
    bubble.innerHTML = marked.parse(content);
  } else {
    bubble.textContent = content;
  }

  // Insert before typing indicator
  if (typingIndicator) {
    container.insertBefore(bubble, typingIndicator);
  } else {
    container.appendChild(bubble);
  }

  // Animate in
  requestAnimationFrame(() => {
    bubble.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    bubble.style.opacity = '1';
    bubble.style.transform = 'translateY(0)';
  });

  scrollToBottom();
}

async function clearChat() {
  if (!confirm('Clear your entire chat history with Aria?')) return;
  try {
    await fetch('/chat/clear', { method: 'POST' });
    const container = document.getElementById('chatMessages');
    container.innerHTML = `
      <div class="chat-bubble assistant" id="welcomeMsg">
        <strong>👋 Chat history cleared!</strong>
        <p>Hi! I'm Aria, your EduPilot AI Learning Coach. How can I help you today? 🚀</p>
      </div>
      <div class="typing-indicator" id="typingIndicator" style="display:none;">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
        <span style="font-size:.78rem;color:var(--text-muted);margin-left:4px;">Aria is thinking...</span>
      </div>
    `;
    document.getElementById('chatSuggestions').style.display = '';
    document.getElementById('chatSuggestions').style.opacity = '1';
  } catch (e) {
    alert('Error clearing chat.');
  }
}
