import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import { getToken, getCurrentUser, clearToken, getGroups, createGroup } from './api'
import './App.css'

function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [groups, setGroups] = useState([])
  const [groupsOpen, setGroupsOpen] = useState(true)
  const [friendsOpen, setFriendsOpen] = useState(true)
  const [creatingGroup, setCreatingGroup] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')

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

  useEffect(() => {
    if (currentUser) {
      loadGroups()
    }
  }, [currentUser])

  async function loadGroups() {
    try {
      const data = await getGroups()
      setGroups(data)
    } catch (err) {
      console.error('Failed to load groups:', err)
    }
  }

  async function handleCreateGroup() {
    if (!newGroupName.trim()) return
    try {
      await createGroup({ name: newGroupName })
      setNewGroupName('')
      setCreatingGroup(false)
      loadGroups()
    } catch (err) {
      alert('Failed to create group: ' + err.message)
    }
  }

  function handleLogout() {
    clearToken()
    setCurrentUser(null)
    setGroups([])
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
              <div>
                <ul className="dropdown-list">
                  {groups.map(g => (
                    <li key={g.id} className="dropdown-item">
                      <span className="item-avatar group-avatar">{g.name[0]}</span>
                      <span className="item-label">{g.name}</span>
                      <span className="item-count">{g.members?.length || 1}</span>
                    </li>
                  ))}
                </ul>
                {creatingGroup ? (
                  <div className="create-group-form">
                    <input
                      type="text"
                      placeholder="Group name"
                      value={newGroupName}
                      onChange={e => setNewGroupName(e.target.value)}
                      onKeyPress={e => e.key === 'Enter' && handleCreateGroup()}
                    />
                    <button onClick={handleCreateGroup}>Create</button>
                    <button onClick={() => setCreatingGroup(false)}>Cancel</button>
                  </div>
                ) : (
                  <button className="add-group-btn" onClick={() => setCreatingGroup(true)}>+ Add Group</button>
                )}
              </div>
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
                <li className="dropdown-item">
                  <span className="item-avatar friend-avatar">FR</span>
                  <span className="item-label">Friends feature coming soon</span>
                </li>
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
        <Dashboard groups={groups} />
      </main>
    </div>
  )
}

export default App