import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import SourceCitation from './SourceCitation';
import '../styles/MessageBubble.css';

export default function MessageBubble({ message, isUser }) {
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
    </div>
  );
}
