import { useState } from 'react'
import './ExpenseForm.css'
import { CATEGORY_COLORS } from '../constants/categories'

const SPLIT_TYPES = [
  { value: 'equal', label: 'Split equally' },
  { value: 'exact', label: 'Exact amounts' },
  { value: 'percentage', label: 'By percentage' },
]

function ExpenseForm({ members, currentUserId, categories = [], onSubmit, onClose, initialValues = null, initialSplits = null }) {
  const isEdit = initialValues !== null
  const [description, setDescription] = useState(initialValues?.description ?? '')
  const [amount, setAmount] = useState(initialValues?.amount ?? '')
  const [expenseDate, setExpenseDate] = useState(
    initialValues?.expense_date
      ? new Date(initialValues.expense_date).toISOString().split('T')[0]
      : new Date().toISOString().split('T')[0]
  )
  const [splitType, setSplitType] = useState(initialValues?.split_type ?? 'equal')
  const [memberSplits, setMemberSplits] = useState(() => {
    if (!initialSplits?.length) return {}
    return Object.fromEntries(initialSplits.map(s => [
      s.user_id,
      { amount: s.share_amount ?? '', percentage: s.share_percentage ?? '' },
    ]))
  })
  const [categoryId, setCategoryId] = useState(initialValues?.category_id ?? 1)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [hoveredCat, setHoveredCat] = useState(null)

  const nonPayers = members.filter(m => m.user_id !== currentUserId).sort((a, b) => (a.display_name || "").localeCompare(b.display_name || ""))

  function updateSplit(userId, field, value) {
    setMemberSplits(prev => ({
      ...prev,
      [userId]: { ...prev[userId], [field]: value },
    }))
  }

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
      expense_date: expenseDate,
      split_type: splitType,
      category_id: categoryId,
    }

    if (splitType === 'percentage') {
      const total = nonPayers.reduce((sum, m) => sum + parseFloat(memberSplits[m.user_id]?.percentage || 0), 0)
      if (Math.round(total * 100) !== 10000) {
        setError(`Percentages must add up to 100% (currently ${total.toFixed(2)}%).`)
        return
      }
    }

    if (splitType === 'exact' || splitType === 'percentage') {
      const field = splitType === 'exact' ? 'amount' : 'percentage'
      body.member_splits = nonPayers.map(m => ({
        user_id: m.user_id,
        [field]: parseFloat(memberSplits[m.user_id]?.[field] || 0),
      }))
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
          <h2>{isEdit ? 'Edit Expense' : 'Add Expense'}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="expense-form">
          <div className="form-group">
            <label>Description</label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="e.g. Dinner, Groceries"
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
              <label>Date</label>
              <input
                type="date"
                value={expenseDate}
                onChange={e => setExpenseDate(e.target.value)}
                required
              />
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

          <div className="form-group">
            <label>Split type</label>
            <div className="split-type-options">
              {SPLIT_TYPES.map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  className={`split-type-btn ${splitType === opt.value ? 'active' : ''}`}
                  onClick={() => setSplitType(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {splitType === 'equal' && (
            <p className="split-hint">
              Split evenly among all {members.length} members.
            </p>
          )}

          {splitType === 'exact' && (
            <div className="form-group">
              <label>Each member owes</label>
              {nonPayers.map(m => (
                <div key={m.user_id} className="split-row">
                  <span className="split-name">{m.display_name}</span>
                  <div className="split-input-wrap">
                    <span className="split-prefix">$</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      value={memberSplits[m.user_id]?.amount || ''}
                      onChange={e => updateSplit(m.user_id, 'amount', e.target.value)}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {splitType === 'percentage' && (
            <div className="form-group">
              <label>Each member's share</label>
              {nonPayers.map(m => (
                <div key={m.user_id} className="split-row">
                  <span className="split-name">{m.display_name}</span>
                  <div className="split-input-wrap">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      placeholder="0"
                      value={memberSplits[m.user_id]?.percentage || ''}
                      onChange={e => updateSplit(m.user_id, 'percentage', e.target.value)}
                    />
                    <span className="split-suffix">%</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && <p className="form-error">{error}</p>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : isEdit ? 'Save Changes' : 'Add Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ExpenseForm