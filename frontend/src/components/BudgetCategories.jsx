import './BudgetCategories.css'

const CATEGORY_COLORS = {
  'Groceries':     '#22c55e',
  'Food & Drink':  '#fb923c',
  'Transport':     '#60a5fa',
  'Housing':       '#a78bfa',
  'Entertainment': '#f472b6',
  'Shopping':      '#facc15',
  'Travel':        '#34d399',
  'Utilities':     '#94a3b8',
  'Health':        '#b45309',
  'Other':         '#cbd5e1',
}

const FALLBACK_COLORS = ['#60a5fa','#4ade80','#fb923c','#a78bfa','#f472b6','#facc15','#34d399','#94a3b8']

function BudgetCategories({ budgets }) {
  const total = budgets.reduce((sum, b) => sum + b.spent, 0)

  return (
    <div className="budget-categories card">
      <div className="card-header">
        <h2>Spending by Category</h2>
        <span className="friends-count">${total.toFixed(2)} total</span>
      </div>
      {budgets.length === 0 ? (
        <p className="budget-empty">No expenses recorded yet.</p>
      ) : (
        <ul>
          {budgets.map((b, i) => {
            const pct = total > 0 ? (b.spent / total) * 100 : 0
            const color = CATEGORY_COLORS[b.category] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length]
            return (
              <li key={b.category} className="budget-item">
                <div className="budget-item-header">
                  <span>{b.icon ? `${b.icon} ${b.category}` : b.category}</span>
                  <span className="budget-amounts">
                    <strong>${b.spent.toFixed(2)}</strong>
                    <span className="budget-pct"> · {pct.toFixed(0)}%</span>
                  </span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${pct}%`, background: color }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

export default BudgetCategories
