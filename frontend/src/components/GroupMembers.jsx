import { useState } from 'react'
import './GroupMembers.css'

function GroupMembers({ members, currentUser, isAdmin, onSettlePayment, onRemoveMember, onTransferAdmin, onLeaveGroup }) {
  const [managing, setManaging] = useState(false)

  return (
    <div className="group-members card">
      <div className="card-header">
        <h2>Group Members</h2>
        <button className="btn-link" onClick={() => setManaging(!managing)}>
          {managing ? 'Done' : 'Manage'}
        </button>
      </div>
      <ul>
        {members.map((m) => (
          <li key={m.id} className="member-item">
            <div className="member-avatar">{m.avatar}</div>
            <div className="member-info">
              <p className="member-name">
                {m.name}
                {m.isAdmin && <span className="role-badge">Admin</span>}
              </p>
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
                        <p className="member-settlement">Paid you: ${m.paymentsToYou.toFixed(2)}</p>
                      )}
                      {m.paymentsFromYou > 0 && (
                        <p className="member-settlement">You paid: ${m.paymentsFromYou.toFixed(2)}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="member-actions">
              {managing && !m.isYou && isAdmin && (
                <>
                  <button className="btn-danger-sm" onClick={() => onRemoveMember(m.id)}>Remove</button>
                  <button className="btn-secondary-sm" onClick={() => onTransferAdmin(m.id)}>Make Admin</button>
                </>
              )}
              {managing && m.isYou && (
                <button className="btn-danger-sm" onClick={onLeaveGroup}>Leave</button>
              )}
              {!managing && !m.isYou && (
                <button
                  className="btn-settle"
                  onClick={() => onSettlePayment(m)}
                  disabled={!m.canSettle}
                >
                  {m.canSettle ? 'Pay back' : 'Await payment'}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default GroupMembers
