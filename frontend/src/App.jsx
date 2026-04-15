import { useState, useEffect } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Profile from './pages/Profile'
import { getToken, getCurrentUser, clearToken, getGroups, createGroup, deleteGroup, joinGroup, getGroupMembers } from './api'
import './App.css'

function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [groups, setGroups] = useState([])
  const [selectedGroupId, setSelectedGroupId] = useState(null)
  const [groupsOpen, setGroupsOpen] = useState(true)
  const [friendsOpen, setFriendsOpen] = useState(true)
  const [creatingGroup, setCreatingGroup] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [joiningGroup, setJoiningGroup] = useState(false)
  const [inviteCode, setInviteCode] = useState('')
  const [showProfile, setShowProfile] = useState(false)

  // On load, restore session from stored token
  useEffect(() => {
    const checkAuth = async () => {
      if (getToken()) {
        try {
          const user = await getCurrentUser()
          setCurrentUser(user)
        } catch (err) {
          console.error('Auth check failed:', err)
          clearToken()
        }
      }
      setAuthChecked(true)
    }
    
    checkAuth()
  }, [])

  useEffect(() => {
    if (currentUser) {
      loadGroups()
    }
  }, [currentUser])

  async function loadGroups() {
    try {
      const data = await getGroups()
      const groupsWithCounts = await Promise.all(
        data.map(async g => {
          try {
            const members = await getGroupMembers(g.id)
            return { ...g, memberCount: members.length }
          } catch (err) {
            console.error('Failed to load group members for', g.id, err)
            return { ...g, memberCount: g.members?.length || 1 }
          }
        })
      )
      setGroups(groupsWithCounts)
      const activeId = groupsWithCounts.find(g => g.id === selectedGroupId)?.id || groupsWithCounts[0]?.id || null
      setSelectedGroupId(activeId)
    } catch (err) {
      console.error('Failed to load groups:', err)
    }
  }

  async function handleCreateGroup() {
    if (!newGroupName.trim()) return
    try {
      await createGroup({ name: newGroupName })
      showToast(`Successfully created ${newGroupName}.`, "success")
      setNewGroupName('')
      setCreatingGroup(false)
      loadGroups()
    } catch (err) {
      showToast(`Failed to create group. See: ${err.message}`, "error")
    }
  }

  async function handleDeleteGroup(groupId) {
    if (!confirm('Are you sure you want to delete this group? This action cannot be undone.')) {
      return
    }
    try {
      await deleteGroup(groupId)
      loadGroups()
      showToast("Successfully deleted group.", "success")
    } catch (err) {
      showToast(`Failed to delete group. See: ${err.message}`, "error")
    }
  }

  async function handleJoinGroup() {
    if (!inviteCode.trim()) return
    try {
      await joinGroup(inviteCode)
      showToast(`Successfully joined group ${inviteCode}.`, "success")
      setInviteCode('')
      setJoiningGroup(false)
      loadGroups()
    } catch (err) {
      showToast(`Failed to join group. See: ${err.message}`, "error")
    }
  }

  async function copyInviteCode(code) {
    try {
      await navigator.clipboard.writeText(code)
      showToast(`Successfully copied group invite code: ${code}.`, "success")
    } catch (err) {
      showToast(`Failed to copy group. See: ${err.message}`, "error")
    }
  }

  function handleProfileUpdate() {
    setShowProfile(true)
  }

  function handleLogout() {
    clearToken()
    setCurrentUser(null)
    setGroups([])
    setSelectedGroupId(null)
  }

  function handleDeleteAccount() {
    setCurrentUser(null)
    setGroups([])
    setSelectedGroupId(null)
    setShowProfile(false)
  }

  function handleSelectGroup(groupId) {
    setSelectedGroupId(groupId)
  }

  if (!authChecked) return null
  if (!currentUser) return <Login onLogin={setCurrentUser} />

  function showToast(message, type = "success") {
    let toast = document.getElementById("global-toast");

    if (!toast) {
      toast = document.createElement("div");
      toast.id = "global-toast";
      toast.className = "toast";
      document.body.appendChild(toast);
    }

    toast.className = "toast";

    toast.classList.add(`toast-${type}`);

    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
      toast.classList.remove("show");
    }, 1500);
  }

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
                    <li
                      key={g.id}
                      className={`dropdown-item ${g.id === selectedGroupId ? 'active' : ''}`}
                      onClick={() => handleSelectGroup(g.id)}
                    >
                      <span className="item-avatar group-avatar">{g.name[0]}</span>
                      <span className="item-label">{g.name}</span>
                      <div className="item-actions">
                        <span className="item-count">{g.memberCount ?? (g.members?.length || 1)}</span>
                        <button 
                          className="btn-share" 
                          onClick={(e) => {
                            e.stopPropagation()
                            copyInviteCode(g.invite_code)
                          }}
                          title="Copy invite code"
                        >
                          📋
                        </button>
                        <button 
                          className="btn-delete" 
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteGroup(g.id)
                          }}
                          title="Delete group"
                        >
                          🗑️
                        </button>
                      </div>
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
                  <button className="add-group-btn" onClick={() => setCreatingGroup(true)}>+ Create Group</button>
                )}
                {joiningGroup ? (
                  <div className="create-group-form">
                    <input
                      type="text"
                      placeholder="Enter invite code"
                      value={inviteCode}
                      onChange={e => setInviteCode(e.target.value)}
                      onKeyPress={e => e.key === 'Enter' && handleJoinGroup()}
                    />
                    <button onClick={handleJoinGroup}>Join</button>
                    <button onClick={() => setJoiningGroup(false)}>Cancel</button>
                  </div>
                ) : (
                  <button className="add-group-btn" onClick={() => setJoiningGroup(true)}>Join Group</button>
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
            <span id="friend-icon"></span>Add Friend
          </button>
          <button className="btn-add" onClick={handleProfileUpdate}>
            <span id="profile-icon"></span>{currentUser.display_name}
          </button>
          <button className="btn-add" onClick={handleLogout} style={{ marginTop: '0.25rem', background: '#fee2e2', color: '#dc2626' }}>
            <span id="logout-icon"></span>Sign Out
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Dashboard groups={groups} selectedGroupId={selectedGroupId} onSelectGroup={handleSelectGroup} />
      </main>
      {showProfile && (
        <Profile
          currentUser={currentUser}
          onUpdate={setCurrentUser}
          onClose={() => setShowProfile(false)}
          onDeleteAccount={handleDeleteAccount}
        />
      )}
    </div>
  )
}

export default App