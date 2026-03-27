import React, { useState, useEffect, useRef } from 'react';
import chatService from '../services/api';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import '../styles/ChatContainer.css';

export default function ChatContainer() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Initialize session on mount
    initializeSession();
  }, []);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages]);

  const initializeSession = async () => {
    try {
      // Check if session exists in localStorage
      const savedSessionId = localStorage.getItem('chat_session_id');

      if (savedSessionId) {
        setSessionId(savedSessionId);
        // Optionally load previous messages
        try {
          const session = await chatService.getSession(savedSessionId);
          const formattedMessages = session.messages.map(msg => ({
            type: msg.message_type,
            content: msg.content,
            sources: msg.sources || [],
            id: msg.id,
          }));
          setMessages(formattedMessages);
        } catch (err) {
          // Session expired or invalid, create new one
          createNewSession();
        }
      } else {
        createNewSession();
      }
    } catch (err) {
      setError('Failed to initialize session');
      console.error(err);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await chatService.createSession();
      const newSessionId = response.session_id;
      setSessionId(newSessionId);
      localStorage.setItem('chat_session_id', newSessionId);
      setMessages([]);
    } catch (err) {
      setError('Failed to create new session');
      console.error(err);
    }
  };

  const handleSendMessage = async (userMessage) => {
    if (!userMessage.trim() || !sessionId) return;

    try {
      setError(null);
      setLoading(true);

      // Add user message to UI immediately
      setMessages(prev => [...prev, {
        type: 'user',
        content: userMessage,
        sources: [],
        id: null,
      }]);

      // Add placeholder for streaming assistant message
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: '',
        sources: [],
        id: null,
      }]);

      await chatService.sendMessageStream(userMessage, sessionId, {
        onChunk: (chunk) => {
          setMessages(prev => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = { ...last, content: last.content + chunk };
            return next;
          });
        },
        onDone: (data) => {
          setMessages(prev => {
            const next = [...prev];
            const last = next[next.length - 1];
            next[next.length - 1] = {
              ...last,
              sources: data.sources || [],
              id: data.message_id ?? last.id,
            };
            return next;
          });
        },
      });
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error(err);
      // Remove user message and empty assistant message if send failed
      setMessages(prev => prev.slice(0, -2));
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    await createNewSession();
    setError(null);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>RAG Chat Assistant</h1>
        <button
          type="button"
          className="new-chat-btn"
          onClick={handleNewChat}
          title="Start a new chat (current conversation will be cleared)"
          aria-label="Start new chat"
        >
          New Chat
        </button>
      </div>

      <div className="messages-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>Welcome to RAG Chat</h2>
            <p>Ask me anything about the documents in our knowledge base.</p>
            <p className="session-id">Session ID: {sessionId?.substring(0, 8)}...</p>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            isUser={message.type === 'user'}
          />
        ))}

        {loading && (!messages.length || messages[messages.length - 1]?.type !== 'assistant') && (
          <div className="loading-bubble">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={loading}
      />
    </div>
  );
}
