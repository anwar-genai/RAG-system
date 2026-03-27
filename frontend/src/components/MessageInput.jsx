import React, { useState } from 'react';
import '../styles/MessageInput.css';

export default function MessageInput({ onSendMessage, disabled }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          className="message-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your question here... (Shift+Enter for new line)"
          disabled={disabled}
          rows="1"
        />
        <button
          type="submit"
          className="send-button"
          disabled={disabled || !input.trim()}
          title="Send message"
        >
          <span>Send</span>
        </button>
      </div>
    </form>
  );
}
