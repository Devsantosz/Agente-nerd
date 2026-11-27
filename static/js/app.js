const $ = (selector) => document.querySelector(selector);
const conversationList = $('#conversation-list');
const messagesEl = $('#messages');
const welcome = $('#welcome');
const chatScroll = $('#chat-scroll');
const input = $('#message-input');
const responseMode = $('#response-mode');
const authGate = $('#auth-gate');
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
let currentId = null;
let busy = false;
let modeChanging = false;
let currentMode = 'normal';
let authMode = 'login';

const modeDescriptions = {
  lite: 'Rápido e econômico',
  normal: 'Equilíbrio entre rapidez e detalhe',
  high: 'Mais análise e explicação',
};

function setModeInUI(mode) {
  currentMode = ['lite', 'normal', 'high'].includes(mode) ? mode : 'normal';
  responseMode.value = currentMode;
  $('#mode-description').textContent = modeDescriptions[currentMode];
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || 'Algo deu errado. Tente novamente.');
    error.status = response.status;
    throw error;
  }
  return data;
}

function showAuthGate() {
  authGate.hidden = false;
  $('#auth-email').focus();
}

async function enterApp(account) {
  authGate.hidden = true;
  $('#profile-name').textContent = 'Minha conta';
  $('#profile-email').textContent = account.email;
  const conversations = await api('/api/conversations');
  if (conversations.length) await openConversation(conversations[0].id);
  else await createConversation();
}

function setAuthMode(mode) {
  authMode = mode;
  document.querySelectorAll('.auth-tab').forEach((tab) => {
    const active = tab.dataset.authMode === mode;
    tab.classList.toggle('active', active);
    tab.setAttribute('aria-selected', String(active));
  });
  const registering = mode === 'register';
  $('#auth-title').textContent = registering ? 'Crie sua conta' : 'Entre para continuar';
  $('#auth-submit').textContent = registering ? 'Criar minha conta' : 'Entrar na minha conta';
  $('#password-hint').hidden = !registering;
  $('#auth-password').autocomplete = registering ? 'new-password' : 'current-password';
  $('#auth-error').textContent = '';
}

document.querySelectorAll('.auth-tab').forEach((tab) => {
  tab.addEventListener('click', () => setAuthMode(tab.dataset.authMode));
});

$('#auth-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const errorEl = $('#auth-error');
  const submit = $('#auth-submit');
  errorEl.textContent = '';
  submit.disabled = true;
  try {
    const result = await api(`/api/auth/${authMode === 'register' ? 'register' : 'login'}`, {
      method: 'POST',
      body: JSON.stringify({
        email: $('#auth-email').value,
        password: $('#auth-password').value,
      }),
    });
    await enterApp(result);
  } catch (error) {
    errorEl.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

$('#logout-button').addEventListener('click', async () => {
  try {
    await api('/api/auth/logout', { method: 'POST', body: '{}' });
    currentId = null;
    showWelcome();
    $('#profile-name').textContent = 'Estudante';
    $('#profile-email').textContent = 'Foco no ENEM 2026';
    showAuthGate();
  } catch (error) {
    toast(error.message);
  }
});

function formatText(text) {
  const escaped = String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  return escaped
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/^### (.*)$/gm, '<strong class="md-heading">$1</strong>')
    .replace(/^## (.*)$/gm, '<strong class="md-heading">$1</strong>')
    .replace(/\n/g, '<br>');
}

function renderMessage(sender, text, pending = false) {
  const row = document.createElement('article');
  row.className = `message-row ${sender === 'usuario' ? 'from-user' : 'from-agent'}`;
  const avatar = sender === 'usuario'
    ? '<div class="message-avatar user-avatar">EU</div>'
    : '<div class="message-avatar agent-avatar">✦</div>';
  row.innerHTML = `${avatar}<div class="message-body"><div class="message-name">${sender === 'usuario' ? 'Você' : 'Pretinho Nerd'}${pending ? '<span class="typing-label"> · pensando</span>' : ''}</div><div class="bubble ${pending ? 'typing' : ''}">${pending ? '<i></i><i></i><i></i>' : formatText(text)}</div></div>`;
  messagesEl.appendChild(row);
  chatScroll.scrollTop = chatScroll.scrollHeight;
  return row;
}

function showChat() {
  welcome.hidden = true;
  messagesEl.classList.add('visible');
  $('#topbar-label').textContent = 'Seu espaço de estudos';
}

function showWelcome() {
  welcome.hidden = false;
  messagesEl.innerHTML = '';
  messagesEl.classList.remove('visible');
  $('#topbar-label').textContent = 'Tutor de estudos';
}

async function refreshConversations() {
  const conversations = await api('/api/conversations');
  conversationList.innerHTML = '';
  $('#history-count').textContent = conversations.length;
  conversations.forEach((conversation) => {
    if (conversation.id === currentId) setModeInUI(conversation.mode);
    const item = document.createElement('div');
    item.className = `conversation-item ${conversation.id === currentId ? 'active' : ''}`;
    const title = document.createElement('button');
    title.className = 'conversation-title';
    title.textContent = conversation.title || 'Nova conversa';
    title.title = conversation.title || 'Nova conversa';
    title.addEventListener('click', () => openConversation(conversation.id));
    const remove = document.createElement('button');
    remove.className = 'delete-conversation';
    remove.type = 'button';
    remove.setAttribute('aria-label', 'Excluir conversa');
    remove.title = 'Excluir conversa';
    remove.textContent = '×';
    remove.addEventListener('click', () => removeConversation(conversation.id));
    item.append(title, remove);
    conversationList.appendChild(item);
  });
}

async function openConversation(id) {
  try {
    currentId = id;
    const conversation = await api(`/api/conversations/${id}/messages`);
    setModeInUI(conversation.mode);
    showChat();
    messagesEl.innerHTML = '';
    if (conversation.messages.length === 0) showWelcome();
    conversation.messages.forEach((message) => renderMessage(message.sender, message.text));
    await refreshConversations();
    closeMobileSidebar();
  } catch (error) { toast(error.message); }
}

async function createConversation() {
  const conversation = await api('/api/conversations', { method: 'POST', body: '{}' });
  currentId = conversation.id;
  setModeInUI(conversation.mode);
  showWelcome();
  await refreshConversations();
  closeMobileSidebar();
  input.focus();
}

responseMode.addEventListener('change', async () => {
  const selectedMode = responseMode.value;
  const targetConversationId = currentId;
  if (!currentId || busy) {
    setModeInUI(currentMode);
    return;
  }
  modeChanging = true;
  $('#send-button').disabled = true;
  responseMode.disabled = true;
  try {
    const result = await api(`/api/conversations/${targetConversationId}/mode`, {
      method: 'POST',
      body: JSON.stringify({ mode: selectedMode }),
    });
    if (currentId === targetConversationId) setModeInUI(result.mode);
  } catch (error) {
    if (currentId === targetConversationId) setModeInUI(currentMode);
    toast(error.message);
  } finally {
    modeChanging = false;
    $('#send-button').disabled = busy;
    responseMode.disabled = false;
  }
});

async function removeConversation(id) {
  try {
    await api(`/api/conversations/${id}`, { method: 'DELETE' });
    const remaining = await api('/api/conversations');
    if (id === currentId) {
      if (remaining.length) await openConversation(remaining[0].id);
      else await createConversation();
    } else await refreshConversations();
  } catch (error) { toast(error.message); }
}

async function sendMessage(value) {
  const text = (value ?? input.value).trim();
  if (!text || busy || modeChanging) return;
  if (!currentId) await createConversation();
  input.value = '';
  input.style.height = 'auto';
  showChat();
  renderMessage('usuario', text);
  const pending = renderMessage('agente', '', true);
  let assistantText = '';
  let ended = false;
  busy = true;
  $('#send-button').disabled = true;
  responseMode.disabled = true;
  try {
    const response = await fetch(`/api/conversations/${currentId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ message: text, mode: currentMode }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const error = new Error(data.error || 'Não foi possível enviar a mensagem.');
      error.status = response.status;
      throw error;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const event = JSON.parse(line.slice(6));
        if (event.type === 'delta') {
          assistantText += event.text;
          const bubble = pending.querySelector('.bubble');
          bubble.classList.remove('typing');
          bubble.innerHTML = formatText(assistantText);
          pending.querySelector('.typing-label')?.remove();
          chatScroll.scrollTop = chatScroll.scrollHeight;
        } else if (event.type === 'status') {
          const label = pending.querySelector('.typing-label');
          if (label) label.textContent = ` · ${event.text}`;
        } else if (event.type === 'error') {
          toast(event.error);
        } else if (event.type === 'done') {
          assistantText = event.text || assistantText;
          ended = true;
          const bubble = pending.querySelector('.bubble');
          bubble.classList.remove('typing');
          bubble.innerHTML = formatText(assistantText);
          pending.querySelector('.typing-label')?.remove();
        }
      }
    }
    if (!ended && !assistantText) throw new Error('A resposta foi interrompida antes de chegar. Tente novamente.');
    await refreshConversations();
  } catch (error) {
    if (error.status === 401) {
      pending.remove();
      showAuthGate();
      return;
    }
    if (!assistantText) {
      pending.remove();
      renderMessage('agente', `Não consegui responder agora. ${error.message}`);
    } else {
      const bubble = pending.querySelector('.bubble');
      bubble.classList.remove('typing');
      bubble.innerHTML = formatText(assistantText);
      pending.querySelector('.typing-label')?.remove();
    }
    toast(error.message);
  } finally {
    busy = false;
    $('#send-button').disabled = false;
    responseMode.disabled = false;
    input.focus();
  }
}

let toastTimer;
function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('visible'), 3500);
}

function openMobileSidebar() {
  $('#sidebar').classList.add('open');
  $('#mobile-scrim').classList.add('visible');
}
function closeMobileSidebar() {
  $('#sidebar').classList.remove('open');
  $('#mobile-scrim').classList.remove('visible');
}

$('#composer').addEventListener('submit', (event) => { event.preventDefault(); sendMessage(); });
input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); }
});
input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 150)}px`; });
$('#new-chat').addEventListener('click', () => createConversation().catch((error) => toast(error.message)));
$('#clear-chat').addEventListener('click', () => createConversation().catch((error) => toast(error.message)));
$('#mobile-menu').addEventListener('click', openMobileSidebar);
$('#mobile-scrim').addEventListener('click', closeMobileSidebar);
document.querySelectorAll('.suggestion').forEach((button) => button.addEventListener('click', () => sendMessage(button.dataset.prompt)));

(async function init() {
  try {
    const account = await api('/api/auth/me');
    if (account.authenticated) await enterApp(account);
    else showAuthGate();
  } catch (error) { toast(error.message); }
})();
