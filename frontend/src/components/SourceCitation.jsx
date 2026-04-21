import React, { useEffect, useRef, useState } from 'react';
import '../styles/SourceCitation.css';

/** Parse "FileName.pdf - Page N" into { name, page } */
function parseSource(source) {
  const match = String(source).match(/^(.+?)\s*-\s*Page\s*(\d+)$/i);
  if (match) return { name: match[1].trim(), page: match[2] };
  return { name: source, page: null };
}

export default function SourceCitation({ sources }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  // Close on outside click / Escape — hooks must run unconditionally.
  useEffect(() => {
    if (!open) return undefined;

    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  if (!sources || sources.length === 0) {
    return null;
  }

  const count = sources.length;

  return (
    <div className="source-citation" ref={containerRef}>
      <button
        type="button"
        className="source-citation__trigger"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={`View ${count} source${count === 1 ? '' : 's'}`}
      >
        <svg
          className="source-citation__trigger-icon"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <path d="M14 2v6h6"></path>
        </svg>
        <span className="source-citation__trigger-text">Sources</span>
        <span className="source-citation__trigger-count">{count}</span>
      </button>

      {open && (
        <div
          className="source-citation__popover"
          role="dialog"
          aria-label="Answer sources"
        >
          <div className="source-citation__popover-header">
            <span className="source-citation__popover-title">Sources</span>
            <button
              type="button"
              className="source-citation__close"
              onClick={() => setOpen(false)}
              aria-label="Close sources"
            >
              ×
            </button>
          </div>
          <div className="source-citation__popover-body">
            {sources.map((source, index) => {
              const { name, page } = parseSource(source);
              return (
                <div key={index} className="source-citation__item" title={source}>
                  <svg
                    className="source-citation__item-icon"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <path d="M14 2v6h6"></path>
                  </svg>
                  <div className="source-citation__item-text">
                    <span className="source-citation__name">{name}</span>
                    {page != null && (
                      <span className="source-citation__page">Page {page}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
