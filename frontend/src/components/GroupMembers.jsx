import './GroupMembers.css'

function GroupMembers({ members }) {
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
              <p className="member-name">{m.name}{m.isYou ? ' (You)' : ''}</p>
              {!m.isYou && (
                <p className={`member-balance ${m.owes > 0 ? 'owes-you' : 'you-owe'}`}>
                  {m.owes > 0
                    ? `Owes you $${m.owes.toFixed(2)}`
                    : `You owe $${Math.abs(m.owes).toFixed(2)}`}
                </p>
              )}
            </div>
            {!m.isYou && (
              <button className="btn-settle">Settle</button>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default GroupMembers