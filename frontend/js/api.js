/**
 * API Service for Document Analyzer
 * Pure JavaScript - No Node.js or TypeScript required.
 */

// Determine API Base URL
function getApiBaseUrl() {
  const stored = localStorage.getItem('DOCUQUERY_API_BASE_URL');
  if (stored) return stored.replace(/\/$/, '');

  // If window.ENV_API_URL was injected
  if (window.ENV_API_URL) return window.ENV_API_URL.replace(/\/$/, '');

  // If served from backend itself (port 8000 or production domain)
  if (window.location.port === '8000') {
    return window.location.origin;
  }

  // If running locally on another port (e.g. 3000, 5500, or file://)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000';
  }

  // Production: use backend URL injected via js/config.js (window.BACKEND_URL)
  // Set window.BACKEND_URL = 'https://your-render-app.onrender.com' in config.js
  if (window.BACKEND_URL) return window.BACKEND_URL.replace(/\/$/, '');

  // No backend URL configured — requests will fail on static hosting.
  // Open Settings (gear icon) in the UI to set the backend URL at runtime.
  console.warn('[DocuQuery] No backend URL configured. Set window.BACKEND_URL in js/config.js or use the Settings panel.');
  return '';
}

class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      const text = await response.text();
      if (text) errorDetail = text;
    }
    throw new ApiError(response.status, errorDetail);
  }
  return response.json();
}

const api = {
  getBaseUrl() {
    return getApiBaseUrl();
  },

  setBaseUrl(url) {
    if (url) {
      localStorage.setItem('DOCUQUERY_API_BASE_URL', url.trim());
    } else {
      localStorage.removeItem('DOCUQUERY_API_BASE_URL');
    }
  },

  async getHealth() {
    const res = await fetch(`${getApiBaseUrl()}/health`);
    return handleResponse(res);
  },

  async getModels() {
    const res = await fetch(`${getApiBaseUrl()}/api/chat/models`);
    return handleResponse(res);
  },

  async getDocuments() {
    const res = await fetch(`${getApiBaseUrl()}/api/documents`);
    const data = await handleResponse(res);
    return data.documents || [];
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${getApiBaseUrl()}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },

  async deleteDocument(documentId) {
    const res = await fetch(`${getApiBaseUrl()}/api/documents/${documentId}`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },

  async getChatHistory(documentId) {
    const key = documentId || 'global';
    const res = await fetch(`${getApiBaseUrl()}/api/chat/history/${key}`);
    const data = await handleResponse(res);
    return data.history || [];
  },

  async clearChatHistory(documentId) {
    const key = documentId || 'global';
    const res = await fetch(`${getApiBaseUrl()}/api/chat/history/${key}`, {
      method: 'DELETE',
    });
    return handleResponse(res);
  },

  async sendMessage(question, documentId, history = [], model = null) {
    const res = await fetch(`${getApiBaseUrl()}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        document_id: documentId || null,
        history,
        model: model || null
      }),
    });
    return handleResponse(res);
  },

  async streamChat(question, documentId, history = [], model = null, callbacks = {}) {
    const { onSources, onToken, onDone, onError } = callbacks;

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          document_id: documentId || null,
          history,
          model: model || null
        }),
      });

      if (!response.ok) {
        let detail = `Streaming error (HTTP ${response.status})`;
        try {
          const errData = await response.json();
          detail = errData.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported by browser.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;
          const jsonStr = trimmed.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);
            if (data.type === 'sources' && onSources) {
              onSources(data.sources || [], data.model);
            } else if (data.type === 'token' && onToken) {
              onToken(data.content);
            } else if (data.type === 'done' && onDone) {
              onDone(data.model);
            } else if (data.type === 'error' && onError) {
              onError(data.message);
            }
          } catch (e) {
            console.error('Failed to parse SSE line:', jsonStr, e);
          }
        }
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Stream connection failed');
      }
    }
  }
};

window.api = api;

