import React, { useState, useRef, useEffect } from 'react';
import '../styles/MessageInput.css';

export default function MessageInput({ onSendMessage, disabled }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px';
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const canSend = !disabled && !!input.trim();

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          className="message-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question… (Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
        />
        <button
          type="submit"
          className={`send-button ${canSend ? 'send-button--active' : ''}`}
          disabled={!canSend}
          title="Send"
        >
          <svg className="send-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M3.4 20.4 20.85 12.9a1 1 0 0 0 0-1.84L3.4 3.56a1 1 0 0 0-1.4 1.05l1.6 6.18a1 1 0 0 0 .77.74L12 12l-7.63 1.47a1 1 0 0 0-.77.74l-1.6 6.18a1 1 0 0 0 1.4 1.01z"/>
          </svg>
        </button>
      </div>
    </form>
  );
}
