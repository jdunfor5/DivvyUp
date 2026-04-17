import { useState } from 'react'
import { updateCurrentUser, deleteCurrentUser, clearToken } from '../api'

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'INR']

export default function Profile({ currentUser, onUpdate, onClose, onDeleteAccount }) {
  const [displayName, setDisplayName] = useState(currentUser.display_name)
  const [avatarEmoji, setAvatarEmoji] = useState(currentUser.avatar_emoji)
  const [avatarColor, setAvatarColor] = useState(currentUser.avatar_color || '#f2e5e7')
  const [phone, setPhone] = useState(currentUser.phone || '')
  const [venmoHandle, setVenmoHandle] = useState(currentUser.venmo_handle || '')
  const [paypalEmail, setPaypalEmail] = useState(currentUser.paypal_email || '')
  const [baseCurrency, setBaseCurrency] = useState(currentUser.base_currency)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deleteError, setDeleteError] = useState(null)

  async function handleDeleteAccount() {
    setDeleteError(null)
    try {
      await deleteCurrentUser()
      clearToken()
      onDeleteAccount()
    } catch (err) {
      setDeleteError(err.message)
      setConfirmingDelete(false)
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const updated = await updateCurrentUser({
        display_name: displayName,
        avatar_emoji: avatarEmoji,
        avatar_color: avatarColor,
        phone: phone || null,
        venmo_handle: venmoHandle || null,
        paypal_email: paypalEmail || null,
        base_currency: baseCurrency,
      })
      onUpdate(updated)
      setSaved(true)
      setTimeout(() => onClose(), 800)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.modal} onClick={e => e.stopPropagation()}>

        <div style={s.header}>
          <h2 style={s.title}>Edit Profile</h2>
          <button style={s.closeBtn} onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit} style={s.form}>

          <div style={s.avatarRow}>
            <div style={{ ...s.avatarPreview, background: avatarColor }}>{avatarEmoji}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <input
                type="text"
                value={avatarEmoji}
                onChange={e => setAvatarEmoji(e.target.value)}
                maxLength={2}
                style={{ ...s.input, width: '70px', textAlign: 'center', fontSize: '20px' }}
                placeholder="😀"
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="color"
                  value={avatarColor}
                  onChange={e => setAvatarColor(e.target.value)}
                  style={s.colorPicker}
                />
                <span style={{ fontSize: '12px', color: '#6b7280' }}>Background color</span>
              </div>
            </div>
          </div>

          <label style={s.label}>Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            required
            style={s.input}
          />

          <label style={s.label}>Phone</label>
          <input
            type="tel"
            value={phone}
            onChange={e => setPhone(e.target.value)}
            placeholder="Optional"
            style={s.input}
          />

          <label style={s.label}>Venmo Handle</label>
          <input
            type="text"
            value={venmoHandle}
            onChange={e => setVenmoHandle(e.target.value)}
            placeholder="@handle"
            style={s.input}
          />

          <label style={s.label}>PayPal Email</label>
          <input
            type="email"
            value={paypalEmail}
            onChange={e => setPaypalEmail(e.target.value)}
            placeholder="Optional"
            style={s.input}
          />

          <label style={s.label}>Base Currency</label>
          <select value={baseCurrency} onChange={e => setBaseCurrency(e.target.value)} style={s.input}>
            {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          {error && <p style={s.error}>{error}</p>}

          <button type="submit" disabled={loading} style={s.submitBtn}>
            {loading ? 'Saving…' : saved ? 'Saved!' : 'Save Changes'}
          </button>

        </form>

        {confirmingDelete ? (
          <div style={s.deleteConfirm}>
            <p style={s.deleteConfirmText}>This will permanently delete your account. Are you sure?</p>
            {deleteError && <p style={s.error}>{deleteError}</p>}
            <div style={s.deleteConfirmBtns}>
              <button onClick={() => setConfirmingDelete(false)} style={s.deleteCancelBtn}>Cancel</button>
              <button onClick={handleDeleteAccount} style={s.deleteConfirmBtn}>Yes, delete</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setConfirmingDelete(true)} style={s.deleteBtn}>
            Delete Account
          </button>
        )}
      </div>
    </div>
  )
}

const s = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.35)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: '#ffffff',
    borderRadius: '14px',
    boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
    padding: '2rem',
    width: '100%',
    maxWidth: '400px',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: '17px',
    fontWeight: '800',
    color: '#111827',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    fontSize: '16px',
    cursor: 'pointer',
    color: '#6b7280',
    padding: '4px 8px',
    borderRadius: '6px',
  },
  avatarRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '1rem',
  },
  avatarPreview: {
    fontSize: '40px',
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  colorPicker: {
    width: '32px',
    height: '32px',
    border: '1.5px solid #e5e7eb',
    borderRadius: '6px',
    cursor: 'pointer',
    padding: '2px',
    background: 'none',
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
    width: '100%',
  },
  error: {
    color: '#ef4444',
    fontSize: '13px',
    fontWeight: '500',
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
  deleteBtn: {
    marginTop: '12px',
    width: '100%',
    padding: '0.65rem',
    borderRadius: '10px',
    border: '1.5px solid #fca5a5',
    background: 'transparent',
    color: '#dc2626',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
  },
  deleteConfirm: {
    marginTop: '12px',
    padding: '12px',
    borderRadius: '10px',
    border: '1.5px solid #fca5a5',
    background: '#fff5f5',
  },
  deleteConfirmText: {
    fontSize: '13px',
    color: '#7f1d1d',
    marginBottom: '10px',
  },
  deleteConfirmBtns: {
    display: 'flex',
    gap: '8px',
  },
  deleteCancelBtn: {
    flex: 1,
    padding: '0.55rem',
    borderRadius: '8px',
    border: '1.5px solid #e5e7eb',
    background: '#fff',
    color: '#374151',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
  },
  deleteConfirmBtn: {
    flex: 1,
    padding: '0.55rem',
    borderRadius: '8px',
    border: 'none',
    background: '#dc2626',
    color: '#fff',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: "'Plus Jakarta Sans', sans-serif",
  },
}
