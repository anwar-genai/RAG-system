import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import SourceCitation from './SourceCitation';
import '../styles/MessageBubble.css';

export default function MessageBubble({ message, isUser, onFeedback }) {
  const vote = message.feedback || 0;
  const canVote = !isUser && message.id && message.content && onFeedback;

  const cast = (target) => {
    const next = vote === target ? 0 : target;
    onFeedback(message.id, vote, next);
  };

  return (
    <div className={`message-wrapper ${isUser ? 'user-message' : 'ai-message'}`}>
      <div className={`message-bubble ${isUser ? 'user' : 'ai'}`}>
        <div className={`message-content ${!isUser ? 'message-content--markdown' : ''}`}>
          {isUser ? (
            <p className="message-content__text">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              components={{
                p: ({ children }) => <p className="message-content__p">{children}</p>,
                h1: ({ children }) => <h1 className="message-content__h1">{children}</h1>,
                h2: ({ children }) => <h2 className="message-content__h2">{children}</h2>,
                h3: ({ children }) => <h3 className="message-content__h3">{children}</h3>,
                ul: ({ children }) => <ul className="message-content__ul">{children}</ul>,
                ol: ({ children }) => <ol className="message-content__ol">{children}</ol>,
                li: ({ children }) => <li className="message-content__li">{children}</li>,
                code: ({ className, children, ...props }) =>
                  className ? (
                    <code className={`message-content__code-block ${className}`.trim()} {...props}>{children}</code>
                  ) : (
                    <code className="message-content__code" {...props}>{children}</code>
                  ),
                pre: ({ children }) => <pre className="message-content__pre">{children}</pre>,
                blockquote: ({ children }) => <blockquote className="message-content__blockquote">{children}</blockquote>,
              }}
            >
              {message.content || ''}
            </ReactMarkdown>
          )}
        </div>
      </div>

      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="sources-container">
          <SourceCitation sources={message.sources} />
        </div>
      )}

      {canVote && (
        <div className="feedback-row">
          <button
            type="button"
            className={`feedback-btn ${vote === 1 ? 'feedback-btn--active feedback-btn--up' : ''}`}
            onClick={() => cast(1)}
            aria-label="Helpful"
            title="Helpful"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
            </svg>
          </button>
          <button
            type="button"
            className={`feedback-btn ${vote === -1 ? 'feedback-btn--active feedback-btn--down' : ''}`}
            onClick={() => cast(-1)}
            aria-label="Not helpful"
            title="Not helpful"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
