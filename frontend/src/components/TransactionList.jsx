import './TransactionList.css'

function TransactionList({ transactions }) {
  return (
    <div className="transaction-list card">
      <div className="card-header">
        <h2>Recent Transactions</h2>
        <button className="btn-link">View all</button>
      </div>
      <ul>
        {transactions.map((tx) => (
          <li key={tx.id} className="transaction-item">
            <div className="transaction-left">
              <div className="transaction-category-dot" data-category={tx.category} />
              <div>
                <p className="transaction-desc">{tx.description}</p>
                <p className="transaction-date">{tx.date} · {tx.category}{tx.paidByName ? ` · Paid by ${tx.paidByName}` : ''}</p>
              </div>
            </div>
            <p className={`transaction-amount ${tx.amount < 0 ? 'negative' : 'positive'}`}>
              {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount).toFixed(2)}
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default TransactionList