import { useState } from 'react'
import './ExpenseForm.css'

const CATEGORY_COLORS = {
  'Groceries':     '#b45309',
  'Food & Drink':  '#f59e0b',
  'Transport':     '#3b82f6',
  'Housing':       '#ef4444',
  'Entertainment': '#8b5cf6',
  'Shopping':      '#ec4899',
  'Travel':        '#06b6d4',
  'Utilities':     '#4f46e5',
  'Health':        '#22c55e',
  'Other':         '#14b8a6',
}

const INTERVALS = [
  { value: 'daily',    label: 'Daily' },
  { value: 'weekly',   label: 'Weekly' },
  { value: 'biweekly', label: 'Every 2 weeks' },
  { value: 'monthly',  label: 'Monthly' },
  { value: 'yearly',   label: 'Yearly' },
]

function RecurringExpenseForm({ categories = [], onSubmit, onClose, initialValues = null }) {
  const isEdit = initialValues !== null
  const [description, setDescription] = useState(initialValues?.description ?? '')
  const [amount, setAmount] = useState(initialValues?.amount ?? '')
  const [categoryId, setCategoryId] = useState(initialValues?.category_id ?? 1)
  const [interval, setInterval] = useState(initialValues?.interval ?? 'monthly')
  const [startDate, setStartDate] = useState(initialValues?.start_date ?? new Date().toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(initialValues?.end_date ?? '')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [hoveredCat, setHoveredCat] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    const base = parseFloat(amount)
    if (!description || isNaN(base) || base <= 0) {
      setError('Description and a valid amount are required.')
      return
    }

    const body = {
      description,
      amount: base,
      base_amount: base,
      currency: 'USD',
      exchange_rate: 1,
      category_id: categoryId,
      split_type: 'equal',
      interval,
      start_date: startDate,
      end_date: endDate || null,
    }

    setSubmitting(true)
    try {
      await onSubmit(body)
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
          <h2>{isEdit ? 'Edit Recurring Expense' : 'Add Recurring Expense'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="expense-form">
          <div className="form-group">
            <label>Description</label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="e.g. Netflix, Rent"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Amount ($)</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={e => setAmount(e.target.value)}
                placeholder="0.00"
                required
              />
            </div>
            <div className="form-group">
              <label>Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>End Date <span style={{ fontWeight: 400, color: 'var(--text-secondary)' }}>(optional)</span></label>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              min={startDate}
            />
          </div>

          <div className="form-group">
            <label>Repeats</label>
            <div className="split-type-options">
              {INTERVALS.map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  className={`split-type-btn ${interval === opt.value ? 'active' : ''}`}
                  onClick={() => setInterval(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {categories.length > 0 && (
            <div className="form-group">
              <label>Category</label>
              <div className="category-options">
                {categories.map(cat => {
                  const color = CATEGORY_COLORS[cat.name] || 'var(--accent)'
                  const isActive = categoryId === cat.id
                  const isHovered = hoveredCat === cat.id
                  const style = isActive
                    ? { background: color, borderColor: color, color: '#fff', boxShadow: `0 2px 8px ${color}66` }
                    : isHovered
                    ? { background: `${color}22`, borderColor: color, color: color }
                    : {}
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      className={`category-btn ${isActive ? 'active' : ''}`}
                      onClick={() => setCategoryId(cat.id)}
                      onMouseEnter={() => setHoveredCat(cat.id)}
                      onMouseLeave={() => setHoveredCat(null)}
                      style={style}
                    >
                      <span className="category-icon">{cat.icon}</span>
                      <span className="category-name">{cat.name}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {error && <p className="form-error">{error}</p>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : isEdit ? 'Save Changes' : 'Add Recurring'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default RecurringExpenseForm