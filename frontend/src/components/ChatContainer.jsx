import React, { useState, useEffect, useRef, useCallback } from 'react';
import chatService from '../services/api';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import '../styles/ChatContainer.css';

const EXAMPLE_PROMPTS = [
  'What are the key topics covered in the documents?',
  'Summarize the main policies in the handbook.',
  'What file formats are supported for upload?',
  'How does the retrieval system work?',
];

export default function ChatContainer({ onLogout, onAdmin, currentUser }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const userMenuRef = useRef(null);

  const isAdmin = currentUser?.role === 'admin';

  const loadSessions = useCallback(async () => {
    try {
      const data = await chatService.listSessions();
      setSessions(data);
    } catch { /* non-critical */ }
  }, []);

  useEffect(() => {
    initializeSession();
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Close user menu on outside click
  useEffect(() => {
    if (!userMenuOpen) return;
    const handler = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [userMenuOpen]);

  const initializeSession = async () => {
    const saved = localStorage.getItem('chat_session_id');
    if (!saved) return; // No session yet — backend will create one on the first message.
    try {
      const session = await chatService.getSession(saved);
      setSessionId(saved);
      setMessages(session.messages.map(m => ({
        type: m.message_type, content: m.content, sources: m.sources || [], id: m.id,
      })));
    } catch {
      // Saved id is stale (e.g. different user logged in on this browser) — drop it.
      localStorage.removeItem('chat_session_id');
      setSessionId(null);
      setMessages([]);
    }
  };

  // "+ New Chat" — reset local state only. The backend session is created on first message.
  const createNewSession = () => {
    setSessionId(null);
    setMessages([]);
    localStorage.removeItem('chat_session_id');
  };

  const switchSession = async (sid) => {
    try {
      const session = await chatService.getSession(sid);
      setSessionId(sid);
      localStorage.setItem('chat_session_id', sid);
      setMessages(session.messages.map(m => ({
        type: m.message_type, content: m.content, sources: m.sources || [], id: m.id,
      })));
      setError(null);
    } catch {
      setError('Could not load session.');
    }
  };

  const handleSendMessage = async (userMessage) => {
    if (!userMessage.trim()) return;
    setError(null);
    setLoading(true);

    // Add user message + empty assistant placeholder together so typing indicator
    // shows until the first chunk arrives and fills the placeholder.
    setMessages(prev => [
      ...prev,
      { type: 'user', content: userMessage, sources: [], id: null },
      { type: 'assistant', content: '', sources: [], id: null },
    ]);

    try {
      await chatService.sendMessageStream(userMessage, sessionId, {
        onChunk: (chunk) => {
          setMessages(prev => {
            const next = [...prev];
            const last = { ...next[next.length - 1] };
            last.content += chunk;
            next[next.length - 1] = last;
            return next;
          });
        },
        onDone: (data) => {
          // Capture the session id the backend created (or re-used) on first turn.
          if (data.session_id && data.session_id !== sessionId) {
            setSessionId(data.session_id);
            localStorage.setItem('chat_session_id', data.session_id);
          }
          setMessages(prev => {
            const next = [...prev];
            next[next.length - 1] = {
              ...next[next.length - 1],
              sources: data.sources || [],
              id: data.message_id ?? null,
            };
            return next;
          });
          loadSessions();
        },
      });
    } catch (err) {
      // Drop the empty assistant placeholder but keep the user's message so
      // they can see what they sent and retry. Use the backend's error text
      // when available (it's already user-friendly).
      setError(err?.message || 'Failed to send message. Please try again.');
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.type === 'assistant' && last.content === '') {
          return prev.slice(0, -1);
        }
        return prev;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFilesSelected = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true);
    setError(null);
    try {
      const result = await chatService.uploadDocuments(files);
      const count = result.uploaded?.length || 0;
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: `✓ ${count} file${count !== 1 ? 's' : ''} uploaded and indexed successfully.${result.skipped?.length ? ` (${result.skipped.length} skipped — unsupported format)` : ''}`,
        sources: [], id: null,
      }]);
    } catch (err) {
      setError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const groupSessions = () => {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
    const groups = { Today: [], Yesterday: [], Earlier: [] };
    sessions.forEach(s => {
      const d = new Date(s.updated_at); d.setHours(0, 0, 0, 0);
      if (d >= today) groups.Today.push(s);
      else if (d >= yesterday) groups.Yesterday.push(s);
      else groups.Earlier.push(s);
    });
    return groups;
  };

  const groups = groupSessions();

  // True only while waiting for the first chunk (assistant placeholder is still empty)
  const waitingForFirstChunk = loading && messages[messages.length - 1]?.type === 'assistant'
    && messages[messages.length - 1]?.content === '';

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar--open' : 'sidebar--closed'}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
              <path d="M8 16C8 11.582 11.582 8 16 8s8 3.582 8 8-3.582 8-8 8-8-3.582-8-8z" fill="white" fillOpacity="0.4"/>
              <path d="M12 16l3 3 5-6" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          {sidebarOpen && <span className="sidebar-logo-text">DocuChat</span>}
        </div>

        {/* New Chat */}
        <button className="new-chat-btn" onClick={() => { createNewSession(); setError(null); }}>
          <span className="new-chat-icon">+</span>
          {sidebarOpen && <span>New Chat</span>}
        </button>

        {/* Session list */}
        {sidebarOpen && (
          <div className="session-list">
            {Object.entries(groups).map(([label, items]) =>
              items.length === 0 ? null : (
                <div key={label} className="session-group">
                  <div className="session-group-label">{label}</div>
                  {items.map(s => (
                    <button
                      key={s.session_id}
                      className={`session-item ${s.session_id === sessionId ? 'session-item--active' : ''}`}
                      onClick={() => switchSession(s.session_id)}
                      title={s.title}
                    >
                      <span className="session-item-title">{s.title}</span>
                      <span className="session-item-count">{s.message_count}</span>
                    </button>
                  ))}
                </div>
              )
            )}
            {sessions.length === 0 && (
              <div className="session-empty">No conversations yet</div>
            )}
          </div>
        )}

        {/* Bottom actions */}
        <div className="sidebar-footer">
          {/* Upload — admin only */}
          {sidebarOpen && isAdmin && (
            <>
              <button
                className="sidebar-action-btn"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                {uploading ? 'Uploading…' : 'Upload Docs'}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md,.docx,.csv"
                style={{ display: 'none' }}
                onChange={handleFilesSelected}
              />
            </>
          )}

          {/* User menu */}
          <div className="sidebar-user-wrap" ref={userMenuRef}>
            {userMenuOpen && (
              <div className="user-menu">
                <div className="user-menu-name">{currentUser?.username || 'User'}</div>
                {isAdmin && onAdmin && (
                  <button
                    className="user-menu-item"
                    onClick={() => { setUserMenuOpen(false); onAdmin(); }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 20h9"/>
                      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                    </svg>
                    Admin Panel
                  </button>
                )}
                <button
                  className="user-menu-item user-menu-item--danger"
                  onClick={() => { setUserMenuOpen(false); onLogout(); }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16 17 21 12 16 7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  Sign out
                </button>
              </div>
            )}
            <button
              className="sidebar-user"
              onClick={() => setUserMenuOpen(o => !o)}
              title="Account menu"
            >
              <div className="sidebar-avatar">
                {(currentUser?.username?.[0] || 'U').toUpperCase()}
              </div>
              {sidebarOpen && (
                <div className="sidebar-user-info">
                  <span className="sidebar-username">{currentUser?.username || 'User'}</span>
                  <span className={`sidebar-role-badge ${isAdmin ? 'badge-admin' : 'badge-user'}`}>
                    {currentUser?.role || 'user'}
                  </span>
                </div>
              )}
              {sidebarOpen && (
                <svg
                  className={`user-menu-chevron ${userMenuOpen ? 'user-menu-chevron--open' : ''}`}
                  width="14" height="14" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2"
                >
                  <polyline points="18 15 12 9 6 15"/>
                </svg>
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main area ───────────────────────────────────── */}
      <main className="main-area">
        {/* Top bar */}
        <header className="topbar">
          <button className="toggle-btn" onClick={() => setSidebarOpen(o => !o)} title="Toggle sidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <span className="topbar-title">
            {sessions.find(s => s.session_id === sessionId)?.title || 'New conversation'}
          </span>
        </header>

        {/* Messages */}
        <div className="messages-area">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="40" height="40" viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="8" fill="#ede9fe"/>
                  <path d="M8 16C8 11.582 11.582 8 16 8s8 3.582 8 8-3.582 8-8 8-8-3.582-8-8z" fill="#a78bfa"/>
                  <path d="M12 16l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h2 className="empty-title">How can I help you today?</h2>
              <p className="empty-sub">Ask a question about your documents or choose an example below.</p>
              <div className="prompt-grid">
                {EXAMPLE_PROMPTS.map(p => (
                  <button key={p} className="prompt-chip" onClick={() => handleSendMessage(p)}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => {
            // Don't render the empty assistant placeholder — typing indicator shows instead
            if (waitingForFirstChunk && i === messages.length - 1 && msg.type === 'assistant') return null;
            return <MessageBubble key={i} message={msg} isUser={msg.type === 'user'} />;
          })}

          {waitingForFirstChunk && (
            <div className="typing-wrap">
              <div className="typing-indicator">
                <span /><span /><span />
              </div>
            </div>
          )}

          {error && <div className="error-toast">{error}</div>}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <MessageInput onSendMessage={handleSendMessage} disabled={loading} />
      </main>
    </div>
  );
}
