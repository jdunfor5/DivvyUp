import './SummaryCard.css'

function SummaryCard({ title, amount, type }) {
  const icons = {
    balance: '💼',
    income: '📈',
    expense: '📉',
    owed: '🤝',
  }

  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(Math.abs(amount))

  return (
    <div className={`summary-card summary-card--${type}`}>
      <div className="summary-card-icon">{icons[type]}</div>
      <div className="summary-card-info">
        <p className="summary-card-title">{title}</p>
        <p className="summary-card-amount">{formatted}</p>
      </div>
    </div>
  )
}

export default SummaryCard