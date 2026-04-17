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
            <div className="member-avatar" style={{ background: m.avatarColor }}>{m.avatar}</div>
            <div className="member-info">
              <p className="member-name">
                {m.name}
                {m.isAdmin && <span className="role-badge">Admin</span>}
              </p>
              {!m.isYou && (
                <div className="member-balance-info">
                  {m.owes !== 0 && (
                    <p className={`member-balance ${m.owes < 0 ? 'owes-you' : 'you-owe'}`}>
                      {m.owes < 0
                        ? `Owes you $${Math.abs(m.owes).toFixed(2)}`
                        : `You owe $${m.owes.toFixed(2)}`}
                    </p>
                  )}
                  {(m.paymentsToYou > 0 || m.paymentsFromYou > 0) && (
                    <div className="member-settlement-tip">
                      <span className="settlement-tip-icon">ℹ</span>
                      <div className="settlement-tip-body">
                        {m.paymentsToYou > 0 && <span>Paid you: ${m.paymentsToYou.toFixed(2)}</span>}
                        {m.paymentsFromYou > 0 && <span>You paid: ${m.paymentsFromYou.toFixed(2)}</span>}
                      </div>
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
              {!managing && !m.isYou && m.canSettle && (
                <button className="btn-settle" onClick={() => onSettlePayment(m)}>
                  Pay back
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
