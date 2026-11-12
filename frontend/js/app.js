/**
 * Main Application Logic for Document Analyzer
 * Pure Vanilla JavaScript - No Node.js or TypeScript required.
 */

// Application State
const state = {
  documents: [],
  selectedDocId: null, // null means "All Documents"
  models: [],
  selectedModel: 'meta-llama/llama-3.3-70b-instruct',
  messages: [],
  isGenerating: false,
  isUploading: false,
  health: null,
};

// DOM Elements
const elements = {
  // Navigation & Health
  healthIndicator: document.getElementById('health-indicator'),
  healthText: document.getElementById('health-text'),
  modelSelect: document.getElementById('model-select'),
  apiUrlBtn: document.getElementById('api-url-btn'),
  
  // Document Management
  dropZone: document.getElementById('drop-zone'),
  fileInput: document.getElementById('file-input'),
  uploadBtn: document.getElementById('upload-btn'),
  uploadProgress: document.getElementById('upload-progress'),
  progressBar: document.getElementById('progress-bar'),
  progressText: document.getElementById('progress-text'),
  documentList: document.getElementById('document-list'),
  docCountBadge: document.getElementById('doc-count-badge'),
  allDocsBtn: document.getElementById('all-docs-btn'),
  
  // Workspace / Header
  activeDocTitle: document.getElementById('active-doc-title'),
  activeDocSubtitle: document.getElementById('active-doc-subtitle'),
  clearChatBtn: document.getElementById('clear-chat-btn'),
  
  // Chat Interface
  chatMessages: document.getElementById('chat-messages'),
  emptyState: document.getElementById('empty-state'),
  chatForm: document.getElementById('chat-form'),
  chatInput: document.getElementById('chat-input'),
  sendBtn: document.getElementById('send-btn'),
  
  // Source Modal
  sourceModal: document.getElementById('source-modal'),
  sourceModalTitle: document.getElementById('source-modal-title'),
  sourceModalMeta: document.getElementById('source-modal-meta'),
  sourceModalContent: document.getElementById('source-modal-content'),
  sourceModalClose: document.getElementById('source-modal-close'),
  
  // Settings Modal
  settingsModal: document.getElementById('settings-modal'),
  settingsInput: document.getElementById('settings-api-input'),
  settingsSave: document.getElementById('settings-save-btn'),
  settingsClose: document.getElementById('settings-close-btn'),
  
  // Mobile toggle
  mobileSidebarToggle: document.getElementById('mobile-sidebar-toggle'),
  sidebar: document.getElementById('sidebar'),
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  setupMarked();
  setupEventListeners();
  await checkHealth();
  await loadModels();
  await loadDocuments();
  updateActiveDocHeader();
});

// Configure Marked.js options
function setupMarked() {
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false,
    });
  }
}

// Event Listeners
function setupEventListeners() {
  // File Upload Drag & Drop
  if (elements.dropZone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      elements.dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        elements.dropZone.classList.remove('drag-active');
      }, false);
    });

    elements.dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        handleFiles(files);
      }
    });

    elements.dropZone.addEventListener('click', () => {
      elements.fileInput.click();
    });
  }

  if (elements.fileInput) {
    elements.fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files);
      }
    });
  }

  // Model Selector
  if (elements.modelSelect) {
    elements.modelSelect.addEventListener('change', (e) => {
      state.selectedModel = e.target.value;
      showToast(`Model switched to ${e.target.options[e.target.selectedIndex].text}`, 'info');
    });
  }

  // All Documents selection button
  if (elements.allDocsBtn) {
    elements.allDocsBtn.addEventListener('click', () => {
      selectDocument(null);
    });
  }

  // Chat Form Submit
  if (elements.chatForm) {
    elements.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSendMessage();
    });
  }

  // Textarea Enter-to-send (Shift+Enter for newline)
  if (elements.chatInput) {
    elements.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    // Auto-resize textarea
    elements.chatInput.addEventListener('input', () => {
      elements.chatInput.style.height = 'auto';
      elements.chatInput.style.height = `${Math.min(elements.chatInput.scrollHeight, 180)}px`;
    });
  }

  // Clear Chat Button
  if (elements.clearChatBtn) {
    elements.clearChatBtn.addEventListener('click', handleClearChat);
  }

  // Modal Closures
  if (elements.sourceModalClose) {
    elements.sourceModalClose.addEventListener('click', closeSourceModal);
  }
  if (elements.sourceModal) {
    elements.sourceModal.addEventListener('click', (e) => {
      if (e.target === elements.sourceModal) closeSourceModal();
    });
  }

  // Settings Modal
  if (elements.apiUrlBtn) {
    elements.apiUrlBtn.addEventListener('click', openSettingsModal);
  }
  if (elements.settingsClose) {
    elements.settingsClose.addEventListener('click', closeSettingsModal);
  }
  if (elements.settingsSave) {
    elements.settingsSave.addEventListener('click', saveSettings);
  }
  if (elements.settingsModal) {
    elements.settingsModal.addEventListener('click', (e) => {
      if (e.target === elements.settingsModal) closeSettingsModal();
    });
  }

  // Mobile Sidebar Toggle
  if (elements.mobileSidebarToggle && elements.sidebar) {
    elements.mobileSidebarToggle.addEventListener('click', () => {
      elements.sidebar.classList.toggle('hidden');
    });
  }

  // Delegate starter prompt click
  document.addEventListener('click', (e) => {
    const promptBtn = e.target.closest('.starter-prompt-btn');
    if (promptBtn) {
      const promptText = promptBtn.getAttribute('data-prompt');
      if (promptText && elements.chatInput) {
        elements.chatInput.value = promptText;
        elements.chatInput.focus();
        handleSendMessage();
      }
    }
  });
}

// Check Backend Health
async function checkHealth() {
  try {
    const health = await api.getHealth();
    state.health = health;

    if (elements.healthIndicator && elements.healthText) {
      elements.healthIndicator.className = 'w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse';
      if (health.openrouter_configured) {
        elements.healthText.textContent = 'API & OpenRouter Ready';
      } else {
        elements.healthIndicator.className = 'w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]';
        elements.healthText.textContent = 'Set OPENROUTER_API_KEY';
      }
    }
  } catch (err) {
    console.warn('Backend health check error:', err);
    if (elements.healthIndicator && elements.healthText) {
      elements.healthIndicator.className = 'w-2.5 h-2.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]';
      elements.healthText.textContent = 'Backend Offline';
    }
  }
}

// Load Models
async function loadModels() {
  try {
    const models = await api.getModels();
    state.models = models;

    if (elements.modelSelect && models.length > 0) {
      elements.modelSelect.innerHTML = '';
      models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} ${model.is_free ? '(Free)' : ''}`;
        if (model.id === state.selectedModel) {
          option.selected = true;
        }
        elements.modelSelect.appendChild(option);
      });
    }
  } catch (err) {
    console.error('Failed to load models:', err);
  }
}

// Load Documents
async function loadDocuments() {
  try {
    const docs = await api.getDocuments();
    state.documents = docs;
    renderDocumentList();
    if (elements.docCountBadge) {
      elements.docCountBadge.textContent = docs.length;
    }
  } catch (err) {
    console.error('Failed to load documents:', err);
    showToast('Failed to load documents: ' + err.message, 'error');
  }
}

// Render Document List in Left Panel
function renderDocumentList() {
  if (!elements.documentList) return;

  if (state.documents.length === 0) {
    elements.documentList.innerHTML = `
      <div class="text-center py-8 px-4 text-slate-500 text-sm">
        <svg class="w-8 h-8 mx-auto mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        No documents indexed yet.<br/>Upload a document above to begin.
      </div>
    `;
    return;
  }

  // Update "All Documents" button active style
  if (elements.allDocsBtn) {
    if (state.selectedDocId === null) {
      elements.allDocsBtn.className = 'w-full flex items-center justify-between p-3 rounded-xl border border-indigo-500/40 bg-indigo-600/15 text-indigo-200 transition-all shadow-[0_0_15px_rgba(99,102,241,0.15)]';
    } else {
      elements.allDocsBtn.className = 'w-full flex items-center justify-between p-3 rounded-xl border border-white/5 bg-slate-900/40 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 hover:border-white/10 transition-all';
    }
  }

  elements.documentList.innerHTML = state.documents.map(doc => {
    const isSelected = state.selectedDocId === doc.id;
    const formattedSize = formatBytes(doc.file_size);
    const dateStr = new Date(doc.uploaded_at).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    const activeClasses = isSelected
      ? 'border-indigo-500/50 bg-indigo-600/15 text-white shadow-[0_0_15px_rgba(99,102,241,0.15)]'
      : 'border-white/5 bg-slate-900/40 text-slate-300 hover:bg-slate-800/50 hover:border-white/10';

    return `
      <div 
        class="group relative rounded-xl border p-3.5 transition-all cursor-pointer ${activeClasses}"
        onclick="selectDocument('${doc.id}')"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="p-2 rounded-lg ${isSelected ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-800 text-slate-400 group-hover:text-indigo-400'}">
              <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="truncate">
              <h4 class="text-sm font-medium truncate ${isSelected ? 'text-indigo-200' : 'text-slate-200'}">${escapeHtml(doc.filename)}</h4>
              <p class="text-xs text-slate-500 mt-0.5">${formattedSize} • ${doc.page_count} pages • ${doc.chunk_count} chunks</p>
            </div>
          </div>
          
          <button 
            type="button" 
            title="Delete document" 
            class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
            onclick="event.stopPropagation(); deleteDocument('${doc.id}', '${escapeHtml(doc.filename)}')"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// Select Document
window.selectDocument = function(docId) {
  state.selectedDocId = docId;
  renderDocumentList();
  updateActiveDocHeader();
};

// Update Workspace Header based on selected document
function updateActiveDocHeader() {
  if (!elements.activeDocTitle || !elements.activeDocSubtitle) return;

  if (state.selectedDocId === null) {
    elements.activeDocTitle.textContent = 'All Indexed Documents';
    elements.activeDocSubtitle.textContent = `Querying unified vector store across ${state.documents.length} document(s)`;
  } else {
    const doc = state.documents.find(d => d.id === state.selectedDocId);
    if (doc) {
      elements.activeDocTitle.textContent = doc.filename;
      elements.activeDocSubtitle.textContent = `Scoped query • ${doc.page_count} pages • ${doc.chunk_count} chunks indexed`;
    }
  }
}

// Handle File Uploads
async function handleFiles(files) {
  if (state.isUploading) return;
  const fileArray = Array.from(files);

  for (const file of fileArray) {
    // Validate extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!['.pdf', '.txt', '.md'].includes(ext)) {
      showToast(`Unsupported file type: ${file.name}. Only PDF, TXT, and MD are supported.`, 'error');
      continue;
    }

    // Validate size (30MB max)
    if (file.size > 30 * 1024 * 1024) {
      showToast(`File ${file.name} exceeds 30MB size limit.`, 'error');
      continue;
    }

    await uploadSingleFile(file);
  }

  // Reset file input
  if (elements.fileInput) elements.fileInput.value = '';
}

async function uploadSingleFile(file) {
  state.isUploading = true;
  showUploadProgress(true, `Reading and indexing ${file.name}...`);

  try {
    const response = await api.uploadDocument(file);
    showToast(`Successfully indexed "${file.name}" with ${response.document.chunk_count} chunks.`, 'success');
    await loadDocuments();
    // Automatically select newly uploaded document
    selectDocument(response.document.id);
  } catch (err) {
    console.error('Upload failed:', err);
    showToast(`Upload failed: ${err.message}`, 'error');
  } finally {
    state.isUploading = false;
    showUploadProgress(false);
  }
}

function showUploadProgress(visible, text = '') {
  if (!elements.uploadProgress) return;
  if (visible) {
    elements.uploadProgress.classList.remove('hidden');
    if (elements.progressText) elements.progressText.textContent = text;
    if (elements.progressBar) elements.progressBar.style.width = '75%';
  } else {
    if (elements.progressBar) elements.progressBar.style.width = '100%';
    setTimeout(() => {
      elements.uploadProgress.classList.add('hidden');
      if (elements.progressBar) elements.progressBar.style.width = '0%';
    }, 400);
  }
}

// Delete Document
window.deleteDocument = async function(docId, filename) {
  if (!confirm(`Are you sure you want to delete "${filename}" and its vector index?`)) {
    return;
  }

  try {
    await api.deleteDocument(docId);
    showToast(`Deleted ${filename}`, 'info');
    if (state.selectedDocId === docId) {
      state.selectedDocId = null;
    }
    await loadDocuments();
    updateActiveDocHeader();
  } catch (err) {
    console.error('Delete failed:', err);
    showToast(`Failed to delete document: ${err.message}`, 'error');
  }
};

// Handle Send Message (Streaming RAG)
async function handleSendMessage() {
  const query = elements.chatInput.value.trim();
  if (!query || state.isGenerating) return;

  // Clear input and reset height
  elements.chatInput.value = '';
  elements.chatInput.style.height = 'auto';

  // Hide empty state
  if (elements.emptyState) {
    elements.emptyState.classList.add('hidden');
  }

  // 1. Append User Message
  appendUserMessage(query);

  // 2. Append Assistant Message Placeholder with typing indicator
  const assistantBubble = appendAssistantMessagePlaceholder();
  state.isGenerating = true;
  updateSendButtonState(true);

  // Buffer for stream
  let streamText = '';
  let retrievedSources = [];

  // Build history for API (last 6 messages)
  const historyPayload = state.messages.slice(-6).map(m => ({
    role: m.role,
    content: m.content
  }));

  try {
    await api.streamChat(
      query,
      state.selectedDocId || undefined,
      historyPayload,
      state.selectedModel,
      {
        onSources: (sources, model) => {
          retrievedSources = sources;
          renderSourcesPills(assistantBubble, sources);
        },
        onToken: (token) => {
          streamText += token;
          updateAssistantStreamContent(assistantBubble, streamText);
          scrollToBottom();
        },
        onDone: (model) => {
          finalizeAssistantMessage(assistantBubble, streamText, retrievedSources, model);
          state.messages.push({ role: 'user', content: query });
          state.messages.push({
            role: 'assistant',
            content: streamText,
            sources: retrievedSources,
            model_used: model
          });
          state.isGenerating = false;
          updateSendButtonState(false);
        },
        onError: (errMsg) => {
          showToast(errMsg, 'error');
          assistantBubble.querySelector('.message-body').innerHTML = `
            <div class="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
              <strong>Error:</strong> ${escapeHtml(errMsg)}
            </div>
          `;
          state.isGenerating = false;
          updateSendButtonState(false);
        }
      }
    );
  } catch (err) {
    console.error('Chat failed:', err);
    showToast(err.message || 'Failed to generate answer', 'error');
    state.isGenerating = false;
    updateSendButtonState(false);
  }
}

function appendUserMessage(text) {
  const msgEl = document.createElement('div');
  msgEl.className = 'flex justify-end mb-6 animate-fadeIn';
  msgEl.innerHTML = `
    <div class="max-w-[85%] md:max-w-[70%] rounded-2xl rounded-tr-sm bg-gradient-to-r from-indigo-600 to-indigo-700 text-white p-4 shadow-lg shadow-indigo-600/15">
      <p class="whitespace-pre-wrap leading-relaxed text-[0.95rem]">${escapeHtml(text)}</p>
    </div>
  `;
  elements.chatMessages.appendChild(msgEl);
  scrollToBottom();
}

function appendAssistantMessagePlaceholder() {
  const msgEl = document.createElement('div');
  msgEl.className = 'flex items-start gap-3 mb-6 animate-fadeIn assistant-message-container';
  msgEl.innerHTML = `
    <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-md shadow-indigo-500/20 mt-1">
      <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    </div>
    
    <div class="flex-1 min-w-0 glass-panel rounded-2xl rounded-tl-sm p-4.5 border border-white/10 shadow-xl">
      <!-- Sources Container -->
      <div class="sources-pill-container flex flex-wrap gap-1.5 mb-3 hidden"></div>

      <!-- Content Body -->
      <div class="message-body markdown-content streaming-cursor">
        <div class="flex items-center gap-1.5 py-2 text-slate-400 text-sm">
          <span class="w-2 h-2 rounded-full bg-indigo-400 typing-dot"></span>
          <span class="w-2 h-2 rounded-full bg-indigo-400 typing-dot"></span>
          <span class="w-2 h-2 rounded-full bg-indigo-400 typing-dot"></span>
          <span class="ml-2 text-xs font-mono text-slate-500">Searching FAISS index & querying OpenRouter...</span>
        </div>
      </div>

      <!-- Action Bar -->
      <div class="action-bar flex items-center justify-between mt-3 pt-3 border-t border-white/5 text-xs text-slate-500 hidden">
        <div class="model-badge font-mono text-[11px] text-slate-400"></div>
        <button type="button" class="copy-btn flex items-center gap-1 hover:text-indigo-400 transition-colors">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span>Copy</span>
        </button>
      </div>
    </div>
  `;
  elements.chatMessages.appendChild(msgEl);
  scrollToBottom();
  return msgEl;
}

function updateAssistantStreamContent(container, text) {
  const body = container.querySelector('.message-body');
  if (body) {
    if (window.marked) {
      body.innerHTML = marked.parse(text);
    } else {
      body.textContent = text;
    }
  }
}

function renderSourcesPills(container, sources) {
  if (!sources || sources.length === 0) return;
  const pillBox = container.querySelector('.sources-pill-container');
  if (!pillBox) return;

  pillBox.classList.remove('hidden');
  pillBox.innerHTML = `
    <span class="text-xs text-slate-400 flex items-center gap-1 mr-1">
      <svg class="w-3 h-3 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      Grounding Sources:
    </span>
    ${sources.map((src, i) => `
      <button 
        type="button" 
        class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/20 text-xs transition-colors"
        onclick='openSourceModal(${JSON.stringify(src).replace(/'/g, "&apos;")})'
      >
        <span class="font-medium truncate max-w-[140px]">${escapeHtml(src.source)}</span>
        ${src.page ? `<span class="opacity-60 text-[10px]">p.${src.page}</span>` : ''}
      </button>
    `).join('')}
  `;
}

function finalizeAssistantMessage(container, fullText, sources, model) {
  const body = container.querySelector('.message-body');
  if (body) {
    body.classList.remove('streaming-cursor');
    if (window.marked) {
      body.innerHTML = marked.parse(fullText);
    }
  }

  const actionBar = container.querySelector('.action-bar');
  if (actionBar) {
    actionBar.classList.remove('hidden');
    const badge = actionBar.querySelector('.model-badge');
    if (badge) badge.textContent = `Model: ${model || state.selectedModel}`;

    const copyBtn = actionBar.querySelector('.copy-btn');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(fullText);
        copyBtn.innerHTML = `
          <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span class="text-emerald-400">Copied!</span>
        `;
        setTimeout(() => {
          copyBtn.innerHTML = `
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span>Copy</span>
          `;
        }, 2000);
      });
    }
  }
}

function updateSendButtonState(isBusy) {
  if (!elements.sendBtn) return;
  elements.sendBtn.disabled = isBusy;
  if (isBusy) {
    elements.sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
  } else {
    elements.sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

// Clear Conversation
async function handleClearChat() {
  if (state.messages.length === 0) return;
  if (!confirm('Clear this conversation history?')) return;

  try {
    await api.clearChatHistory(state.selectedDocId || undefined);
    state.messages = [];
    if (elements.chatMessages) {
      elements.chatMessages.innerHTML = '';
      if (elements.emptyState) {
        elements.chatMessages.appendChild(elements.emptyState);
        elements.emptyState.classList.remove('hidden');
      }
    }
    showToast('Conversation cleared', 'info');
  } catch (err) {
    showToast('Failed to clear chat: ' + err.message, 'error');
  }
}

// Source Citation Modal
window.openSourceModal = function(src) {
  if (!elements.sourceModal) return;
  elements.sourceModalTitle.textContent = src.source || 'Document Excerpt';
  elements.sourceModalMeta.textContent = `Document ID: ${src.document_id} ${src.page ? `• Page ${src.page}` : ''} ${src.chunk_index !== undefined ? `• Chunk #${src.chunk_index}` : ''}`;
  elements.sourceModalContent.textContent = src.content_snippet || 'No excerpt available.';
  elements.sourceModal.classList.remove('hidden');
};

function closeSourceModal() {
  if (elements.sourceModal) {
    elements.sourceModal.classList.add('hidden');
  }
}

// Settings Modal (API URL Configuration)
function openSettingsModal() {
  if (!elements.settingsModal) return;
  if (elements.settingsInput) {
    elements.settingsInput.value = api.getBaseUrl();
  }
  elements.settingsModal.classList.remove('hidden');
}

function closeSettingsModal() {
  if (elements.settingsModal) {
    elements.settingsModal.classList.add('hidden');
  }
}

async function saveSettings() {
  const newUrl = elements.settingsInput.value.trim();
  api.setBaseUrl(newUrl);
  closeSettingsModal();
  showToast('Backend API URL saved', 'success');
  await checkHealth();
  await loadDocuments();
}

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="flex-1">${escapeHtml(message)}</div>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Utilities
function scrollToBottom() {
  if (elements.chatMessages) {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }
}

function formatBytes(bytes, decimals = 1) {
  if (!+bytes) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function escapeHtml(string) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(string));
  return div.innerHTML;
}

