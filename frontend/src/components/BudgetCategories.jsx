import { useState } from 'react'
import './BudgetCategories.css'
import { CATEGORY_COLORS } from '../constants/categories'

const FALLBACK_COLORS = ['#60a5fa','#4ade80','#fb923c','#a78bfa','#f472b6','#facc15','#34d399','#94a3b8']

const TABS = [
  { key: 'all',       label: 'All' },
  { key: 'oneTime',   label: 'One-time' },
  { key: 'recurring', label: 'Recurring' },
]

function BudgetCategories({ budgets = [], oneTimeBudgets = [], recurringBudgets = [] }) {
  const [activeTab, setActiveTab] = useState('all')

  const dataMap = { all: budgets, oneTime: oneTimeBudgets, recurring: recurringBudgets }
  const data = dataMap[activeTab]
  const total = data.reduce((sum, b) => sum + b.spent, 0)

  return (
    <div className="budget-categories card">
      <div className="card-header">
        <h2>Spending by Category</h2>
        <span className="friends-count">${total.toFixed(2)} total</span>
      </div>

      <div className="budget-tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`budget-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {data.length === 0 ? (
        <p className="budget-empty">No expenses recorded yet.</p>
      ) : (
        <ul>
          {data.map((b, i) => {
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
