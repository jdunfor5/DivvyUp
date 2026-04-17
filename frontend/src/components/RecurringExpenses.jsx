import './RecurringExpenses.css'
import { CATEGORY_COLORS } from '../constants/categories'

const INTERVAL_LABELS = {
  daily: 'Daily',
  weekly: 'Weekly',
  biweekly: 'Every 2 weeks',
  monthly: 'Monthly',
  yearly: 'Yearly',
}

const SPLIT_LABELS = {
  equal: 'Equal split',
  exact: 'Exact amounts',
  percentage: '% split',
}

function RecurringExpenses({ recurringExpenses, categories = [], onDeactivate, onEdit }) {
  const active = recurringExpenses.filter(r => r.is_active)

  return (
    <div className="recurring-expenses card">
      <div className="card-header">
        <h2>Recurring Expenses</h2>
      </div>

      {active.length === 0 ? (
        <p className="no-recurring">No recurring expenses set up.</p>
      ) : (
        <ul className="recurring-list">
          {active.map(r => {
            const categoryName = categories.find(c => c.id === r.category_id)?.name || 'Misc'
            const color = CATEGORY_COLORS[categoryName] || '#cbd5e1'
            return (
              <li key={r.id} className="recurring-item" style={{ borderLeft: `5px solid ${color}` }}>
                <div className="recurring-info">
                  <p className="recurring-description">{r.description}</p>
                  <p className="recurring-meta">
                    <span className="recurring-amount">${Number(r.amount).toFixed(2)}</span> &middot; {INTERVAL_LABELS[r.interval]} &middot; {categoryName} &middot; {SPLIT_LABELS[r.split_type] || 'Equal split'}
                  </p>
                  <p className="recurring-meta">
                    Next: {r.next_due_date}
                  </p>
                  {r.end_date && (
                    <p className="recurring-meta">
                      Ends: {r.end_date}
                    </p>
                  )}
                </div>
                <div className="recurring-actions">
                  <button
                    className="btn-edit"
                    onClick={() => onEdit(r)}
                    title="Edit"
                  >
                    ✎
                  </button>
                  <button
                    className="btn-delete"
                    onClick={() => onDeactivate(r.id)}
                    title="Deactivate"
                  >
                    ✕
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

export default RecurringExpenses