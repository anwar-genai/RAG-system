import React, { useState, useEffect, useCallback } from 'react';
import memoryService from '../services/memory';

export default function MemorySettings({ onClose }) {
  const [bioInput, setBioInput] = useState('');
  const [prefsInput, setPrefsInput] = useState('{}');
  const [profileMsg, setProfileMsg] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileLoading, setProfileLoading] = useState(true);

  const [memories, setMemories] = useState([]);
  const [memoriesLoading, setMemoriesLoading] = useState(true);
  const [newMem, setNewMem] = useState('');
  const [addingMem, setAddingMem] = useState(false);
  const [memErr, setMemErr] = useState(null);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    try {
      const p = await memoryService.getProfile();
      setBioInput(p.bio || '');
      setPrefsInput(JSON.stringify(p.preferences || {}, null, 2));
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const loadMemories = useCallback(async () => {
    setMemoriesLoading(true);
    try {
      const list = await memoryService.list();
      setMemories(list);
    } finally {
      setMemoriesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
    loadMemories();
  }, [loadProfile, loadMemories]);

  const saveProfile = async () => {
    setProfileMsg(null);
    let prefs;
    try {
      prefs = prefsInput.trim() ? JSON.parse(prefsInput) : {};
    } catch {
      setProfileMsg({ type: 'error', text: 'Preferences must be valid JSON.' });
      return;
    }
    if (typeof prefs !== 'object' || Array.isArray(prefs) || prefs === null) {
      setProfileMsg({ type: 'error', text: 'Preferences must be a JSON object.' });
      return;
    }
    setSavingProfile(true);
    try {
      await memoryService.updateProfile({ bio: bioInput, preferences: prefs });
      setProfileMsg({ type: 'ok', text: 'Saved.' });
    } catch (e) {
      setProfileMsg({ type: 'error', text: e.response?.data?.error || 'Failed to save.' });
    } finally {
      setSavingProfile(false);
    }
  };

  const addMemory = async () => {
    const content = newMem.trim();
    if (!content) return;
    setAddingMem(true);
    setMemErr(null);
    try {
      await memoryService.add(content);
      setNewMem('');
      await loadMemories();
    } catch (e) {
      setMemErr(e.response?.data?.error || 'Failed to add memory.');
    } finally {
      setAddingMem(false);
    }
  };

  const deleteMemory = async (id) => {
    try {
      await memoryService.remove(id);
      setMemories(ms => ms.filter(m => m.id !== id));
    } catch (e) {
      setMemErr(e.response?.data?.error || 'Failed to delete memory.');
    }
  };

  return (
    <div style={s.shell}>
      <header style={s.header}>
        <div>
          <h1 style={s.h1}>Memory & personalization</h1>
          <div style={s.sub}>What the assistant knows about you, used to personalize replies.</div>
        </div>
        <button style={s.closeBtn} onClick={onClose}>Close</button>
      </header>

      <section style={s.section}>
        <h2 style={s.h2}>Profile</h2>
        <p style={s.help}>A short description of who you are and how you'd like the assistant to reply.</p>

        <label style={s.label}>Bio</label>
        <textarea
          style={s.textarea}
          rows={4}
          value={bioInput}
          onChange={e => setBioInput(e.target.value)}
          placeholder="e.g. I'm a dentist in Dubai building a patient intake form."
          maxLength={2000}
          disabled={profileLoading}
        />

        <label style={{ ...s.label, marginTop: 12 }}>Preferences (JSON)</label>
        <textarea
          style={{ ...s.textarea, fontFamily: 'ui-monospace, monospace', fontSize: 13 }}
          rows={4}
          value={prefsInput}
          onChange={e => setPrefsInput(e.target.value)}
          placeholder='{"tone": "concise"}'
          disabled={profileLoading}
        />

        <div style={s.actionsRow}>
          <button
            style={{ ...s.primaryBtn, opacity: savingProfile ? 0.6 : 1 }}
            onClick={saveProfile}
            disabled={savingProfile || profileLoading}
          >
            {savingProfile ? 'Saving…' : 'Save profile'}
          </button>
          {profileMsg && (
            <span style={{ ...s.msg, color: profileMsg.type === 'ok' ? '#059669' : '#dc2626' }}>
              {profileMsg.text}
            </span>
          )}
        </div>
      </section>

      <section style={s.section}>
        <h2 style={s.h2}>Memories</h2>
        <p style={s.help}>
          Durable facts auto-extracted from your chats. You can add your own; PII and secrets are rejected.
        </p>

        <div style={s.addRow}>
          <textarea
            style={s.addInput}
            rows={2}
            value={newMem}
            onChange={e => setNewMem(e.target.value)}
            placeholder="e.g. User prefers short, terse replies."
            maxLength={240}
          />
          <button
            style={{ ...s.primaryBtn, opacity: (addingMem || !newMem.trim()) ? 0.6 : 1 }}
            onClick={addMemory}
            disabled={addingMem || !newMem.trim()}
          >
            {addingMem ? 'Adding…' : 'Add'}
          </button>
        </div>
        {memErr && <div style={{ ...s.msg, color: '#dc2626', marginBottom: 12 }}>{memErr}</div>}

        {memoriesLoading ? (
          <div style={s.empty}>Loading…</div>
        ) : memories.length === 0 ? (
          <div style={s.empty}>No memories yet. Tell the assistant about yourself in chat, or add one above.</div>
        ) : (
          <div style={s.list}>
            {memories.map(m => (
              <div key={m.id} style={s.row}>
                <div style={s.rowMain}>
                  <div style={s.rowContent}>{m.content}</div>
                  <div style={s.rowMeta}>
                    <span style={s.badge(m.source)}>{m.source}</span>
                    <span>{new Date(m.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                  </div>
                </div>
                <button style={s.deleteBtn} onClick={() => deleteMemory(m.id)} title="Delete memory">×</button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

const s = {
  shell: { maxWidth: 760, margin: '0 auto', padding: '32px 24px', minHeight: '100vh', background: '#f8fafc' },
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24, gap: 12 },
  h1: { fontSize: 24, fontWeight: 700, margin: 0, color: '#0f172a' },
  h2: { fontSize: 16, fontWeight: 600, margin: '0 0 4px', color: '#0f172a' },
  sub: { fontSize: 13, color: '#64748b', marginTop: 4 },
  help: { fontSize: 13, color: '#64748b', margin: '0 0 12px' },
  closeBtn: { padding: '8px 16px', border: '1px solid #e2e8f0', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#475569', whiteSpace: 'nowrap' },
  section: { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: 20, marginBottom: 16 },
  label: { display: 'block', fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 },
  textarea: { width: '100%', boxSizing: 'border-box', padding: 10, border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 14, color: '#0f172a', resize: 'vertical', fontFamily: 'inherit' },
  actionsRow: { display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 },
  primaryBtn: { padding: '8px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  msg: { fontSize: 13 },
  addRow: { display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 12 },
  addInput: { flex: 1, padding: 10, border: '1px solid #cbd5e1', borderRadius: 6, fontSize: 14, resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box' },
  list: { display: 'flex', flexDirection: 'column', gap: 8 },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, padding: 12, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6 },
  rowMain: { flex: 1, minWidth: 0 },
  rowContent: { fontSize: 14, color: '#0f172a', marginBottom: 6, lineHeight: 1.4, wordBreak: 'break-word' },
  rowMeta: { display: 'flex', gap: 8, alignItems: 'center', fontSize: 11, color: '#64748b' },
  badge: (source) => ({
    padding: '1px 6px', borderRadius: 3, fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
    background: source === 'manual' ? '#dbeafe' : '#fef3c7',
    color: source === 'manual' ? '#1e40af' : '#92400e',
  }),
  deleteBtn: { width: 28, height: 28, padding: 0, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 4, cursor: 'pointer', fontSize: 18, color: '#dc2626', flexShrink: 0 },
  empty: { fontSize: 13, color: '#64748b', padding: 24, textAlign: 'center' },
};
