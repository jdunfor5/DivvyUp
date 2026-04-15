import { useState } from 'react'
import './SettlementForm.css'

const PROVIDERS = [
  { value: 'cash',   label: 'Cash' },
  { value: 'venmo',  label: 'Venmo' },
  { value: 'paypal', label: 'PayPal' },
  { value: 'other',  label: 'Other' },
]

function SettlementForm({ payee, maxAmount, onSubmit, onClose }) {
  const [amount, setAmount] = useState(maxAmount ? maxAmount.toFixed(2) : '')
  const [provider, setProvider] = useState('cash')
  const [note, setNote] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    const parsed = parseFloat(amount)
    if (isNaN(parsed) || parsed <= 0) {
      setError('Please enter a valid amount.')
      return
    }
    if (maxAmount && parsed > maxAmount) {
      setError(`Amount cannot exceed $${maxAmount.toFixed(2)}.`)
      return
    }

    setSubmitting(true)
    try {
      await onSubmit({
        amount: parsed,
        currency: 'USD',
        provider,
        note: note.trim() || null,
      })
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Record Payment</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="settlement-form">
          <div className="settlement-payee">
            <div className="settlement-payee-avatar">{payee.avatar || payee.initials}</div>
            <div>
              <p className="settlement-payee-label">Paying</p>
              <p className="settlement-payee-name">{payee.name}</p>
            </div>
          </div>

          <div className="form-group">
            <label>Amount ($)</label>
            <div className="amount-input-wrap">
              <span className="split-prefix">$</span>
              <input
                type="number"
                min="0.01"
                max={maxAmount || undefined}
                step="0.01"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                placeholder="0.00"
                required
                autoFocus
              />
            </div>
            {maxAmount && (
              <p className="amount-hint">
                You owe <strong>${maxAmount.toFixed(2)}</strong> — you can pay partially.
              </p>
            )}
          </div>

          <div className="form-group">
            <label>Payment method</label>
            <div className="provider-options">
              {PROVIDERS.map(p => (
                <button
                  key={p.value}
                  type="button"
                  className={`provider-btn ${provider === p.value ? 'active' : ''}`}
                  onClick={() => setProvider(p.value)}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Note <span className="label-optional">(optional)</span></label>
            <input
              type="text"
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="e.g. for last week's dinner"
              maxLength={200}
            />
          </div>

          {error && <p className="form-error">{error}</p>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Recording...' : 'Record Payment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SettlementForm
