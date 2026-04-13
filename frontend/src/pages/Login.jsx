import { useState } from 'react'
import { login, getCurrentUser, api } from '../api'

export default function Login({ onLogin }) {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (mode === 'signup') {
        await api('/users/', {
          method: 'POST',
          body: JSON.stringify({ email, password, display_name: displayName }),
        })
      }
      await login(email, password)
      const user = await getCurrentUser()
      onLogin(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function switchMode(next) {
    setMode(next)
    setError(null)
    setEmail('')
    setPassword('')
    setDisplayName('')
    setShowPassword(false)
  }

  return (
    <div style={s.page}>
      <div style={s.card}>

        {/* Logo */}
        <div style={s.logoRow}>
          <span style={s.logoIcon}>💰</span>
          <span style={s.logoText}>DivvyUp</span>
        </div>

        {/* Tab toggle */}
        <div style={s.tabs}>
          <button
            style={{ ...s.tab, ...(mode === 'login' ? s.tabActive : {}) }}
            onClick={() => switchMode('login')}
            type="button"
          >
            Sign in
          </button>
          <button
            style={{ ...s.tab, ...(mode === 'signup' ? s.tabActive : {}) }}
            onClick={() => switchMode('signup')}
            type="button"
          >
            Sign up
          </button>
        </div>

        <form onSubmit={handleSubmit} style={s.form}>

          {mode === 'signup' && (
            <>
              <label style={s.label}>Display name</label>
              <input
                type="text"
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                placeholder="Your name"
                required
                style={s.input}
              />
            </>
          )}

          <label style={s.label}>Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            style={s.input}
          />

          <label style={s.label}>Password</label>
          <div style={s.passwordRow}>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={{ ...s.input, flex: 1, marginBottom: 0 }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(v => !v)}
              style={s.eyeBtn}
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>

          {error && <p style={s.error}>{error}</p>}

          <button type="submit" disabled={loading} style={s.submitBtn}>
            {loading
              ? (mode === 'signup' ? 'Creating account…' : 'Signing in…')
              : (mode === 'signup' ? 'Create account' : 'Sign in')}
          </button>
        </form>

        <p style={s.switchText}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            style={s.switchLink}
            onClick={() => switchMode(mode === 'login' ? 'signup' : 'login')}
          >
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>

      </div>
    </div>
  )
}

const s = {
  page: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    background: '#f7ebe9',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
  },
  card: {
    background: '#ffffff',
    borderRadius: '14px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)',
    padding: '2.25rem 2rem',
    width: '100%',
    maxWidth: '380px',
    border: '1px solid rgba(0,0,0,0.04)',
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    marginBottom: '1.5rem',
  },
  logoIcon: {
    fontSize: '20px',
    background: '#f2e5e7',
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: '20px',
    fontWeight: '800',
    color: '#111827',
    letterSpacing: '-0.5px',
  },
  tabs: {
    display: 'flex',
    borderRadius: '10px',
    background: '#f7e9eb',
    padding: '4px',
    marginBottom: '1.5rem',
    gap: '4px',
  },
  tab: {
    flex: 1,
    padding: '8px',
    border: 'none',
    borderRadius: '8px',
    background: 'transparent',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
    fontSize: '14px',
    fontWeight: '600',
    color: '#6b7280',
    cursor: 'pointer',
    transition: 'background 0.15s, color 0.15s',
  },
  tabActive: {
    background: '#ffffff',
    color: '#7D323F',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#374151',
    marginTop: '6px',
  },
  input: {
    padding: '0.65rem 0.9rem',
    borderRadius: '10px',
    border: '1.5px solid #e5e7eb',
    fontSize: '14px',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
    outline: 'none',
    color: '#111827',
    background: '#fff',
  },
  passwordRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  eyeBtn: {
    background: 'none',
    border: '1.5px solid #e5e7eb',
    borderRadius: '10px',
    padding: '0.6rem 0.75rem',
    cursor: 'pointer',
    fontSize: '16px',
    lineHeight: 1,
    flexShrink: 0,
  },
  submitBtn: {
    marginTop: '10px',
    padding: '0.75rem',
    borderRadius: '10px',
    border: 'none',
    background: '#9A4F59',
    color: '#fff',
    fontSize: '14px',
    fontWeight: '700',
    cursor: 'pointer',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
    transition: 'background 0.15s',
  },
  error: {
    color: '#ef4444',
    fontSize: '13px',
    marginTop: '2px',
    fontWeight: '500',
  },
  switchText: {
    textAlign: 'center',
    marginTop: '1.25rem',
    fontSize: '13px',
    color: '#6b7280',
  },
  switchLink: {
    background: 'none',
    border: 'none',
    color: '#7D323F',
    fontWeight: '700',
    fontSize: '13px',
    cursor: 'pointer',
    fontFamily: "'Plus Jakarta Sans', sans-serif',",
    padding: 0,
  },
}