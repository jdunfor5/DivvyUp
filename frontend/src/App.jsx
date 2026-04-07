import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import { getToken, getCurrentUser, clearToken } from './api'
import './App.css'

const mockGroups = [
  { id: 1, name: 'Apartment', memberCount: 3 },
  { id: 2, name: 'Trip to Vegas', memberCount: 5 },
  { id: 3, name: 'Work Lunch', memberCount: 4 },
]

const mockFriends = [
  { id: 1, name: 'Alex', initials: 'AX' },
  { id: 2, name: 'Jordan', initials: 'JO' },
  { id: 3, name: 'Casey', initials: 'CA' },
]

function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [groupsOpen, setGroupsOpen] = useState(true)
  const [friendsOpen, setFriendsOpen] = useState(true)

  // On load, restore session from stored token
  useEffect(() => {
    if (getToken()) {
      getCurrentUser()
        .then(setCurrentUser)
        .catch(() => clearToken())
        .finally(() => setAuthChecked(true))
    } else {
      setAuthChecked(true)
    }
  }, [])

  function handleLogout() {
    clearToken()
    setCurrentUser(null)
  }

  if (!authChecked) return null
  if (!currentUser) return <Login onLogin={setCurrentUser} />

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">💰</div>
          <span className="logo-text">DivvyUp</span>
        </div>

        <div className="sidebar-sections">

          {/* Groups Dropdown */}
          <div className="sidebar-dropdown">
            <button
              className={`dropdown-toggle ${groupsOpen ? 'open' : ''}`}
              onClick={() => setGroupsOpen(o => !o)}
            >
              <span className="dropdown-toggle-left">
                <span className="nav-icon">👥</span>
                <span>Groups</span>
              </span>
              <span className="chevron">{groupsOpen ? '▾' : '▸'}</span>
            </button>
            {groupsOpen && (
              <ul className="dropdown-list">
                {mockGroups.map(g => (
                  <li key={g.id} className="dropdown-item">
                    <span className="item-avatar group-avatar">{g.name[0]}</span>
                    <span className="item-label">{g.name}</span>
                    <span className="item-count">{g.memberCount}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Friends Dropdown */}
          <div className="sidebar-dropdown">
            <button
              className={`dropdown-toggle ${friendsOpen ? 'open' : ''}`}
              onClick={() => setFriendsOpen(o => !o)}
            >
              <span className="dropdown-toggle-left">
                <span className="nav-icon">🙋</span>
                <span>Friends</span>
              </span>
              <span className="chevron">{friendsOpen ? '▾' : '▸'}</span>
            </button>
            {friendsOpen && (
              <ul className="dropdown-list">
                {mockFriends.map(f => (
                  <li key={f.id} className="dropdown-item">
                    <span className="item-avatar friend-avatar">{f.initials}</span>
                    <span className="item-label">{f.name}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

        </div>

        {/* Bottom buttons */}
        <div className="sidebar-bottom">
          <button className="btn-add">
            <span>+</span> Add Friend
          </button>
          <button className="btn-add btn-add--group">
            <span>+</span> Add Group
          </button>
          <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#aaa', textAlign: 'center' }}>
            {currentUser.display_name}
          </div>
          <button className="btn-add" onClick={handleLogout} style={{ marginTop: '0.25rem', background: '#fee2e2', color: '#dc2626' }}>
            Sign out
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Dashboard />
      </main>
    </div>
  )
}

export default App