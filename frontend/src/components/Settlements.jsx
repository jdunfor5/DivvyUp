import './Settlements.css'

function Settlements({ settlements, currentUserId, members = [], onConfirmSettlement, onCancelSettlement }) {
  function getMemberName(userId) {
    return members.find(m => m.user_id === userId)?.display_name || 'Someone'
  }
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
              const isToYou = settlement.payee_id === currentUserId
              const payerName = getMemberName(settlement.payer_id)
              const payeeName = getMemberName(settlement.payee_id)
              const provider = settlement.provider ? ` via ${settlement.provider}` : ''
              const description = isFromYou
                ? `You sent ${payeeName} $${settlement.amount}${provider}`
                : isToYou
                ? `${payerName} sent you $${settlement.amount}${provider}`
                : `${payerName} sent ${payeeName} $${settlement.amount}${provider}`

              return (
                <li key={settlement.id} className="settlement-item">
                  <div className="settlement-info">
                    <p className="settlement-description">
                      {description}
                    </p>
                    <p className="settlement-date">
                      {new Date(settlement.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {isToYou && (
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
              const isToYou = settlement.payee_id === currentUserId
              const payerName = getMemberName(settlement.payer_id)
              const payeeName = getMemberName(settlement.payee_id)
              const provider = settlement.provider ? ` via ${settlement.provider}` : ''
              const description = isFromYou
                ? `You paid ${payeeName} $${settlement.amount}${provider}`
                : isToYou
                ? `${payerName} paid you $${settlement.amount}${provider}`
                : `${payerName} paid ${payeeName} $${settlement.amount}${provider}`

              return (
                <li key={settlement.id} className="settlement-item completed">
                  <div className="settlement-info">
                    <p className="settlement-description">
                      {description}
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