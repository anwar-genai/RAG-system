import React, { useState, useEffect, useCallback } from 'react';
import adminService from '../services/admin';

// ─── Helpers ────────────────────────────────────────────────────────────────

function fmt(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ─── Stat Card ───────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{ ...s.card, borderTop: `4px solid ${color}` }}>
      <div style={{ ...s.statValue, color }}>{value}</div>
      <div style={s.statLabel}>{label}</div>
      {sub && <div style={s.statSub}>{sub}</div>}
    </div>
  );
}

// ─── Overview Tab ────────────────────────────────────────────────────────────

function OverviewTab({ stats, error }) {
  if (error) return <div style={s.errorBanner}>{error}</div>;
  if (!stats) return <div style={s.loading}>Loading stats…</div>;
  return (
    <div>
      <div style={s.grid}>
        <StatCard label="Total Users" value={stats.total_users} sub={`${stats.active_users} active`} color="#4f46e5" />
        <StatCard label="Chat Sessions" value={stats.total_sessions} color="#0891b2" />
        <StatCard label="Messages Sent" value={stats.total_messages} color="#059669" />
        <StatCard label="Documents" value={stats.total_documents} sub={fmt(stats.kb_size_bytes)} color="#d97706" />
      </div>
    </div>
  );
}

// ─── Users Tab ───────────────────────────────────────────────────────────────

function UsersTab({ currentUserId }) {
  const [users, setUsers] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    adminService.getUsers().then(setUsers).catch(() => setError('Failed to load users.'));
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleRole = async (u) => {
    const newRole = u.role === 'admin' ? 'user' : 'admin';
    setBusy(u.id);
    try {
      await adminService.updateUser(u.id, { role: newRole });
      load();
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to update role.');
    } finally { setBusy(null); }
  };

  const toggleActive = async (u) => {
    setBusy(u.id);
    try {
      await adminService.updateUser(u.id, { is_active: !u.is_active });
      load();
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to update status.');
    } finally { setBusy(null); }
  };

  const deleteUser = async (u) => {
    if (!window.confirm(`Delete user "${u.username}"? This cannot be undone.`)) return;
    setBusy(u.id);
    try {
      await adminService.deleteUser(u.id);
      load();
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to delete user.');
    } finally { setBusy(null); }
  };

  if (!users) return <div style={s.loading}>Loading users…</div>;

  return (
    <div>
      {error && <div style={s.errorBanner}>{error}<button style={s.clearBtn} onClick={() => setError('')}>✕</button></div>}
      <div style={s.tableWrap}>
        <table style={s.table}>
          <thead>
            <tr>
              {['Username', 'Role', 'Status', 'Sessions', 'Messages', 'Joined', 'Actions'].map(h => (
                <th key={h} style={s.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={s.tr}>
                <td style={s.td}>
                  <span style={s.username}>{u.username}</span>
                  {u.id === currentUserId && <span style={s.youBadge}>you</span>}
                </td>
                <td style={s.td}>
                  <span style={{ ...s.badge, ...(u.role === 'admin' ? s.badgeAdmin : s.badgeUser) }}>
                    {u.role}
                  </span>
                </td>
                <td style={s.td}>
                  <span style={{ ...s.badge, ...(u.is_active ? s.badgeActive : s.badgeInactive) }}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={{ ...s.td, textAlign: 'center' }}>{u.session_count}</td>
                <td style={{ ...s.td, textAlign: 'center' }}>{u.message_count}</td>
                <td style={s.td}>{fmtDate(u.date_joined)}</td>
                <td style={s.td}>
                  <div style={s.actions}>
                    <button
                      style={s.actionBtn}
                      disabled={busy === u.id}
                      onClick={() => toggleRole(u)}
                      title={u.role === 'admin' ? 'Demote to User' : 'Promote to Admin'}
                    >
                      {u.role === 'admin' ? '↓ User' : '↑ Admin'}
                    </button>
                    {u.id !== currentUserId && (
                      <>
                        <button
                          style={{ ...s.actionBtn, ...(u.is_active ? s.btnWarn : s.btnSuccess) }}
                          disabled={busy === u.id}
                          onClick={() => toggleActive(u)}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          style={{ ...s.actionBtn, ...s.btnDanger }}
                          disabled={busy === u.id}
                          onClick={() => deleteUser(u)}
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Documents Tab ───────────────────────────────────────────────────────────

function DocumentsTab() {
  const [docs, setDocs] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    adminService.getDocuments().then(setDocs).catch(() => setError('Failed to load documents.'));
  }, []);

  useEffect(() => { load(); }, [load]);

  const deleteDoc = async (name) => {
    if (!window.confirm(`Delete "${name}" from the knowledge base?`)) return;
    setBusy(name);
    try {
      await adminService.deleteDocument(name);
      load();
    } catch (e) {
      setError(e?.response?.data?.error || 'Failed to delete document.');
    } finally { setBusy(null); }
  };

  const typeColor = { PDF: '#dc2626', TXT: '#2563eb', MD: '#7c3aed', DOCX: '#0891b2', CSV: '#059669' };

  if (!docs) return <div style={s.loading}>Loading documents…</div>;

  return (
    <div>
      {error && <div style={s.errorBanner}>{error}<button style={s.clearBtn} onClick={() => setError('')}>✕</button></div>}
      {docs.length === 0 ? (
        <div style={s.empty}>No documents in the knowledge base yet. Upload files from the chat interface.</div>
      ) : (
        <div style={s.tableWrap}>
          <table style={s.table}>
            <thead>
              <tr>
                {['File Name', 'Type', 'Size', 'Status', 'Uploaded By', 'Date', 'Actions'].map(h => (
                  <th key={h} style={s.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {docs.map(doc => (
                <tr key={doc.name} style={s.tr}>
                  <td style={s.td}><span style={s.filename}>{doc.name}</span></td>
                  <td style={s.td}>
                    <span style={{ ...s.badge, background: typeColor[doc.file_type] || '#6b7280', color: '#fff' }}>
                      {doc.file_type}
                    </span>
                  </td>
                  <td style={s.td}>{fmt(doc.size_bytes)}</td>
                  <td style={s.td}>
                    <span style={{ ...s.badge, ...(doc.status === 'indexed' ? s.badgeActive : s.badgeFailed) }}>
                      {doc.status}
                    </span>
                  </td>
                  <td style={s.td}>{doc.uploaded_by}</td>
                  <td style={s.td}>{fmtDate(doc.uploaded_at)}</td>
                  <td style={s.td}>
                    <button
                      style={{ ...s.actionBtn, ...s.btnDanger }}
                      disabled={busy === doc.name}
                      onClick={() => deleteDoc(doc.name)}
                    >
                      {busy === doc.name ? 'Deleting…' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function AdminPanel({ currentUser, onClose }) {
  const [tab, setTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState('');

  const isAdmin = currentUser?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) return;
    adminService.getStats()
      .then((data) => { setStats(data); setStatsError(''); })
      .catch((e) => {
        if (e?.response?.status === 403) setStatsError("You don't have permission to view admin stats.");
        else setStatsError(e?.response?.data?.error || 'Failed to load stats. Is the backend running?');
      });
  }, [isAdmin]);

  if (!isAdmin) {
    return (
      <div style={s.page}>
        <div style={s.header}>
          <div>
            <h1 style={s.headerTitle}>Admin Panel</h1>
            <p style={s.headerSub}>Manage users, documents, and system settings</p>
          </div>
          <button style={s.backBtn} onClick={onClose}>← Back to Chat</button>
        </div>
        <div style={s.content}>
          <div style={s.errorBanner}>
            You don't have admin permissions. If you believe this is a mistake, please sign out and back in.
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'users', label: 'Users' },
    { id: 'documents', label: 'Documents' },
  ];

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <div>
          <h1 style={s.headerTitle}>Admin Panel</h1>
          <p style={s.headerSub}>Manage users, documents, and system settings</p>
        </div>
        <button style={s.backBtn} onClick={onClose}>← Back to Chat</button>
      </div>

      {/* Tab bar */}
      <div style={s.tabBar}>
        {tabs.map(t => (
          <button
            key={t.id}
            style={{ ...s.tabBtn, ...(tab === t.id ? s.tabActive : {}) }}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={s.content}>
        {tab === 'overview' && <OverviewTab stats={stats} error={statsError} />}
        {tab === 'users' && <UsersTab currentUserId={currentUser?.id} />}
        {tab === 'documents' && <DocumentsTab />}
      </div>
    </div>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const s = {
  page: { minHeight: '100vh', background: '#f8fafc', fontFamily: 'system-ui, sans-serif' },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '24px 32px', background: 'linear-gradient(135deg, #1e1b4b 0%, #4f46e5 100%)',
  },
  headerTitle: { margin: 0, fontSize: '22px', fontWeight: 700, color: '#fff' },
  headerSub: { margin: '4px 0 0', fontSize: '13px', color: 'rgba(255,255,255,0.7)' },
  backBtn: {
    padding: '8px 18px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.3)',
    background: 'rgba(255,255,255,0.1)', color: '#fff', cursor: 'pointer', fontSize: '14px',
    fontWeight: 500,
  },
  tabBar: {
    display: 'flex', gap: '4px', padding: '16px 32px 0',
    borderBottom: '1px solid #e2e8f0', background: '#fff',
  },
  tabBtn: {
    padding: '10px 20px', border: 'none', background: 'none', cursor: 'pointer',
    fontSize: '14px', fontWeight: 500, color: '#64748b', borderRadius: '8px 8px 0 0',
    transition: 'all 0.15s',
  },
  tabActive: {
    color: '#4f46e5', background: '#ede9fe', borderBottom: '2px solid #4f46e5',
  },
  content: { padding: '28px 32px', maxWidth: '1200px', margin: '0 auto' },

  // Stats grid
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' },
  card: {
    background: '#fff', borderRadius: '12px', padding: '20px 24px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  },
  statValue: { fontSize: '32px', fontWeight: 700, margin: '0 0 4px' },
  statLabel: { fontSize: '13px', color: '#64748b', fontWeight: 500 },
  statSub: { fontSize: '12px', color: '#94a3b8', marginTop: '2px' },

  // Table
  tableWrap: { overflowX: 'auto', borderRadius: '12px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' },
  table: { width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: '12px' },
  th: {
    padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 600,
    color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em',
    background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
  },
  tr: { borderBottom: '1px solid #f1f5f9' },
  td: { padding: '12px 16px', fontSize: '14px', color: '#1e293b', verticalAlign: 'middle' },

  // Badges
  badge: { display: 'inline-block', padding: '2px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600 },
  badgeAdmin: { background: '#ede9fe', color: '#5b21b6' },
  badgeUser: { background: '#f1f5f9', color: '#475569' },
  badgeActive: { background: '#dcfce7', color: '#15803d' },
  badgeInactive: { background: '#fef2f2', color: '#dc2626' },
  badgeFailed: { background: '#fef2f2', color: '#dc2626' },

  username: { fontWeight: 600 },
  youBadge: {
    marginLeft: '6px', fontSize: '11px', padding: '1px 6px', borderRadius: '8px',
    background: '#dbeafe', color: '#1d4ed8', fontWeight: 600,
  },
  filename: { fontWeight: 500, fontFamily: 'monospace', fontSize: '13px' },

  // Buttons
  actions: { display: 'flex', gap: '6px', flexWrap: 'wrap' },
  actionBtn: {
    padding: '5px 12px', borderRadius: '6px', border: '1px solid #e2e8f0',
    background: '#f8fafc', color: '#374151', fontSize: '12px', fontWeight: 500,
    cursor: 'pointer',
  },
  btnWarn: { background: '#fff7ed', borderColor: '#fed7aa', color: '#c2410c' },
  btnSuccess: { background: '#f0fdf4', borderColor: '#bbf7d0', color: '#15803d' },
  btnDanger: { background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626' },

  // Misc
  loading: { padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: '15px' },
  empty: { padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: '15px' },
  errorBanner: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626',
    padding: '10px 16px', borderRadius: '8px', marginBottom: '16px', fontSize: '14px',
  },
  clearBtn: { background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: '16px' },
};
