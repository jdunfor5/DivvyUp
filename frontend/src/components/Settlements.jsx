import './Settlements.css'

function Settlements({ settlements, currentUserId, onConfirmSettlement, onCancelSettlement }) {
  const pendingSettlements = settlements.filter(s => s.status === 'pending')
  const completedSettlements = settlements.filter(s => s.status === 'completed')

  if (settlements.length === 0) {
    return (
      <div className="settlements card">
        <div className="card-header">
          <h2>Settlements</h2>
        </div>
        <p className="no-settlements">No settlement history yet.</p>
      </div>
    )
  }

  return (
    <div className="settlements card">
      <div className="card-header">
        <h2>Settlements</h2>
      </div>

      {pendingSettlements.length > 0 && (
        <div className="settlements-section">
          <h3>Pending Confirmation</h3>
          <ul className="settlements-list">
            {pendingSettlements.map((settlement) => {
              const isFromYou = settlement.payer_id === currentUserId
              const otherUser = isFromYou ? settlement.payee_id : settlement.payer_id
              const action = isFromYou ? 'sent' : 'received'

              return (
                <li key={settlement.id} className="settlement-item">
                  <div className="settlement-info">
                    <p className="settlement-description">
                      {isFromYou ? 'You' : 'Someone'} {action} ${settlement.amount} 
                      {settlement.provider && ` via ${settlement.provider}`}
                    </p>
                    <p className="settlement-date">
                      {new Date(settlement.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {!isFromYou && (
                    <div className="settlement-actions">
                      <button 
                        className="btn-confirm"
                        onClick={() => onConfirmSettlement(settlement.id)}
                      >
                        Confirm
                      </button>
                      <button 
                        className="btn-cancel"
                        onClick={() => onCancelSettlement(settlement.id)}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {completedSettlements.length > 0 && (
        <div className="settlements-section">
          <h3>Completed</h3>
          <ul className="settlements-list">
            {completedSettlements.map((settlement) => {
              const isFromYou = settlement.payer_id === currentUserId
              const action = isFromYou ? 'paid' : 'received'

              return (
                <li key={settlement.id} className="settlement-item completed">
                  <div className="settlement-info">
                    <p className="settlement-description">
                      {isFromYou ? 'You' : 'Someone'} {action} ${settlement.amount}
                      {settlement.provider && ` via ${settlement.provider}`}
                    </p>
                    <p className="settlement-date">
                      {new Date(settlement.settled_at || settlement.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}

export default Settlements