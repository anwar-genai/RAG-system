import React, { useState } from 'react';
import authService from '../services/auth';

export default function LoginForm({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const switchMode = (next) => {
    setMode(next);
    setError('');
    setUsername('');
    setPassword('');
    setConfirmPassword('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (mode === 'register' && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'register') {
        await authService.register(username, password);
      }
      await authService.login(username, password);
      onLogin();
    } catch (err) {
      const msg = err?.response?.data?.error || err?.response?.data?.detail || 'Something went wrong. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const isLogin = mode === 'login';

  return (
    <div style={s.root}>
      {/* Left branding panel */}
      <div style={s.brand}>
        <div style={s.brandInner}>
          <div style={s.logo}>
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="white" fillOpacity="0.15" />
              <path d="M8 16C8 11.582 11.582 8 16 8s8 3.582 8 8-3.582 8-8 8-8-3.582-8-8z" fill="white" fillOpacity="0.3" />
              <path d="M12 16l3 3 5-6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span style={s.logoText}>DocuChat</span>
          </div>
          <h1 style={s.brandHeading}>Your documents,<br />answered instantly.</h1>
          <p style={s.brandSub}>Upload any document and get precise, cited answers powered by AI. Built for teams that need reliable information fast.</p>
          <div style={s.features}>
            {['Source-cited answers', 'Secure & private', 'Multi-format support', 'Team management'].map(f => (
              <div key={f} style={s.feature}>
                <span style={s.featureDot} />
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div style={s.formPanel}>
        <div style={s.formInner}>
          <div style={s.formHeader}>
            <h2 style={s.formTitle}>{isLogin ? 'Welcome back' : 'Create your account'}</h2>
            <p style={s.formSub}>{isLogin ? 'Sign in to your workspace' : 'Get started for free'}</p>
          </div>

          <form onSubmit={handleSubmit} style={s.form}>
            <div style={s.field}>
              <label style={s.label}>Username</label>
              <input
                style={s.input}
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>

            <div style={s.field}>
              <label style={s.label}>Password</label>
              <input
                style={s.input}
                type="password"
                placeholder={isLogin ? 'Enter your password' : 'At least 8 characters'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete={isLogin ? 'current-password' : 'new-password'}
                required
              />
            </div>

            {!isLogin && (
              <div style={s.field}>
                <label style={s.label}>Confirm password</label>
                <input
                  style={s.input}
                  type="password"
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                />
              </div>
            )}

            {error && <div style={s.error}>{error}</div>}

            <button style={{ ...s.btn, opacity: loading ? 0.7 : 1 }} type="submit" disabled={loading}>
              {loading
                ? (isLogin ? 'Signing in…' : 'Creating account…')
                : (isLogin ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          <p style={s.toggle}>
            {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
            <button style={s.toggleLink} type="button" onClick={() => switchMode(isLogin ? 'register' : 'login')}>
              {isLogin ? 'Register' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

const s = {
  root: {
    display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  // Left panel
  brand: {
    flex: '0 0 45%', background: 'linear-gradient(160deg, #0f172a 0%, #1e1b4b 60%, #312e81 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 48px',
  },
  brandInner: { maxWidth: '380px' },
  logo: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '48px' },
  logoText: { fontSize: '20px', fontWeight: 700, color: '#fff', letterSpacing: '-0.3px' },
  brandHeading: {
    fontSize: '36px', fontWeight: 800, color: '#fff', lineHeight: 1.2,
    margin: '0 0 20px', letterSpacing: '-0.5px',
  },
  brandSub: { fontSize: '15px', color: 'rgba(255,255,255,0.6)', lineHeight: 1.7, margin: '0 0 36px' },
  features: { display: 'flex', flexDirection: 'column', gap: '12px' },
  feature: { display: 'flex', alignItems: 'center', gap: '10px', color: 'rgba(255,255,255,0.8)', fontSize: '14px' },
  featureDot: { width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', flexShrink: 0 },

  // Right panel
  formPanel: {
    flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: '#f8fafc', padding: '48px 32px',
  },
  formInner: { width: '100%', maxWidth: '400px' },
  formHeader: { marginBottom: '32px' },
  formTitle: { fontSize: '26px', fontWeight: 700, color: '#0f172a', margin: '0 0 6px', letterSpacing: '-0.3px' },
  formSub: { fontSize: '14px', color: '#64748b', margin: 0 },
  form: { display: 'flex', flexDirection: 'column', gap: '18px' },
  field: { display: 'flex', flexDirection: 'column', gap: '6px' },
  label: { fontSize: '13px', fontWeight: 600, color: '#374151' },
  input: {
    padding: '11px 14px', borderRadius: '8px', border: '1.5px solid #e2e8f0',
    fontSize: '15px', color: '#0f172a', background: '#fff', outline: 'none',
    transition: 'border-color 0.15s',
  },
  btn: {
    padding: '12px', borderRadius: '8px', border: 'none',
    background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
    color: '#fff', fontSize: '15px', fontWeight: 600, cursor: 'pointer',
    marginTop: '4px', transition: 'opacity 0.15s',
  },
  error: {
    padding: '10px 14px', borderRadius: '8px', background: '#fef2f2',
    border: '1px solid #fecaca', color: '#dc2626', fontSize: '13px',
  },
  toggle: { marginTop: '24px', textAlign: 'center', fontSize: '14px', color: '#64748b' },
  toggleLink: {
    background: 'none', border: 'none', color: '#4f46e5', fontWeight: 600,
    cursor: 'pointer', fontSize: '14px', padding: 0,
  },
};
