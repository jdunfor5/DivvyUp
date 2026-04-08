import './GroupMembers.css'

function GroupMembers({ members, onSettlePayment }) {
  return (
    <div className="group-members card">
      <div className="card-header">
        <h2>Group Members</h2>
        <button className="btn-link">Manage</button>
      </div>
      <ul>
        {members.map((m) => (
          <li key={m.id} className="member-item">
            <div className="member-avatar">{m.initials}</div>
            <div className="member-info">
              <p className="member-name">{m.name}</p>
              {!m.isYou && (
                <div className="member-balance-info">
                  <p className={`member-balance ${m.owes < 0 ? 'owes-you' : 'you-owe'}`}>
                    {m.owes < 0
                      ? `Owes you $${Math.abs(m.owes).toFixed(2)}`
                      : `You owe $${m.owes.toFixed(2)}`}
                  </p>
                  {(m.paymentsToYou > 0 || m.paymentsFromYou > 0) && (
                    <div className="member-settlements">
                      {m.paymentsToYou > 0 && (
                        <p className="member-settlement">
                          Paid you: ${m.paymentsToYou.toFixed(2)}
                        </p>
                      )}
                      {m.paymentsFromYou > 0 && (
                        <p className="member-settlement">
                          You paid: ${m.paymentsFromYou.toFixed(2)}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
            {!m.isYou && (
              <button 
                className="btn-settle" 
                onClick={() => onSettlePayment(m)}
                disabled={!m.canSettle}
              >
                {m.canSettle ? 'Pay back' : 'Await payment'}
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default GroupMembers