import './BudgetCategories.css'

function BudgetCategories({ budgets }) {
  return (
    <div className="budget-categories card">
      <div className="card-header">
        <h2>Budget Categories</h2>
        <button className="btn-link">Edit</button>
      </div>
      <ul>
        {budgets.map((b) => {
          const pct = Math.min((b.spent / b.limit) * 100, 100)
          const isOver = b.spent > b.limit * 0.85
          return (
            <li key={b.category} className="budget-item">
              <div className="budget-item-header">
                <span>{b.category}</span>
                <span className="budget-amounts">
                  <strong>${b.spent.toFixed(2)}</strong> / ${b.limit}
                </span>
              </div>
              <div className="progress-bar">
                <div
                  className={`progress-fill ${isOver ? 'warning' : ''}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default BudgetCategories