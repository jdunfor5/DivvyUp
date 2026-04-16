import { useEffect, useMemo, useState } from 'react'
import { addFriend, getFriends, removeFriend, searchUsersByEmail } from '../api'

function formatCurrency(value) {
  return `$${Math.abs(Number(value || 0)).toFixed(2)}`
}

function formatAddedDate(value) {
  if (!value) return 'Added recently'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Added recently'
  return `Added ${date.toLocaleDateString()}`
}

function getInitials(name = '') {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function getFriendStatus(balance) {
  const amount = Number(balance || 0)

  if (amount > 0) {
    return {
      label: 'Owes you',
      tone: 'success',
      note: 'This friend owes you.',
    }
  }

  if (amount < 0) {
    return {
      label: 'You owe',
      tone: 'warning',
      note: 'You currently owe this friend money.',
    }
  }

  return {
    label: 'Settled',
    tone: 'neutral',
    note: 'No open balance between you right now.',
  }
}

function FriendsTab({ currentUser, groups = [] }) {
  const [friends, setFriends] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [friendQuery, setFriendQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchingUsers, setSearchingUsers] = useState(false)
  const [submittingFriendId, setSubmittingFriendId] = useState(null)
  const [removingFriendId, setRemovingFriendId] = useState(null)
  const [searchFeedback, setSearchFeedback] = useState('')

  useEffect(() => {
    loadFriends()
  }, [])

  useEffect(() => {
    const trimmedQuery = friendQuery.trim()

    if (!trimmedQuery) {
      setSearchResults([])
      setSearchFeedback('')
      return
    }

    const timeoutId = setTimeout(async () => {
      setSearchingUsers(true)
      try {
        const users = await searchUsersByEmail(trimmedQuery)
        const filteredUsers = users.filter(user => user.id !== currentUser?.id)
        setSearchResults(filteredUsers)
        setSearchFeedback(filteredUsers.length ? '' : 'No users found for that email search.')
      } catch (err) {
        setSearchResults([])
        setSearchFeedback(err.message || 'Failed to search users.')
      } finally {
        setSearchingUsers(false)
      }
    }, 350)

    return () => clearTimeout(timeoutId)
  }, [friendQuery, currentUser?.id])

  async function loadFriends() {
    setLoading(true)
    try {
      const data = await getFriends()
      setFriends(data)
      setError('')
    } catch (err) {
      setError(err.message || 'Failed to load friends.')
    } finally {
      setLoading(false)
    }
  }

  async function handleAddFriend(friendId) {
    setSubmittingFriendId(friendId)
    try {
      await addFriend(friendId)
      setFriendQuery('')
      setSearchResults([])
      setSearchFeedback('Friend added successfully.')
      await loadFriends()
    } catch (err) {
      setSearchFeedback(err.message || 'Failed to add friend.')
    } finally {
      setSubmittingFriendId(null)
    }
  }

  async function handleRemoveFriend(friendId) {
    if (!confirm('Remove this friend from your list?')) return

    setRemovingFriendId(friendId)
    try {
      await removeFriend(friendId)
      await loadFriends()
    } catch (err) {
      setError(err.message || 'Failed to remove friend.')
    } finally {
      setRemovingFriendId(null)
    }
  }

  const normalizedQuery = search.trim().toLowerCase()

  const filteredFriends = useMemo(() => {
    return friends.filter(friend => {
      if (!normalizedQuery) return true
      return (
        friend.display_name.toLowerCase().includes(normalizedQuery) ||
        friend.email.toLowerCase().includes(normalizedQuery)
      )
    })
  }, [friends, normalizedQuery])

  const stats = useMemo(() => {
    return friends.reduce(
      (acc, friend) => {
        const balance = Number(friend.balance || 0)
        acc.totalFriends += 1
        if (balance > 0) acc.owedToYou += balance
        if (balance < 0) acc.youOwe += Math.abs(balance)
        if (balance > 0) acc.friendsWhoOwe += 1
        return acc
      },
      { totalFriends: 0, owedToYou: 0, youOwe: 0, friendsWhoOwe: 0 }
    )
  }, [friends])

  const existingFriendIds = useMemo(() => new Set(friends.map(friend => friend.id)), [friends])

  return (
    <section className="friends-tab">
      <div className="friends-hero card">
        <div>
          <p className="friends-eyebrow">Friends</p>
          <h1>Manage your shared expense circle</h1>
          <p className="friends-subtitle">
            Review balances, find people by email, and keep your friends list up to date.
          </p>
        </div>
        <div className="friends-hero-actions">
          <label className="friends-search">
            <span>Filter current friends</span>
            <input
              type="text"
              placeholder="Search by name or email"
              value={search}
              onChange={event => setSearch(event.target.value)}
            />
          </label>
        </div>
      </div>

      <div className="friends-summary-grid">
        <article className="card friends-summary-card">
          <span>Total friends</span>
          <strong>{stats.totalFriends}</strong>
          <small>People currently connected to your account</small>
        </article>
        <article className="card friends-summary-card">
          <span>Owed to you</span>
          <strong>{formatCurrency(stats.owedToYou)}</strong>
          <small>Open balances where friends owe you</small>
        </article>
        <article className="card friends-summary-card">
          <span>You owe</span>
          <strong>{formatCurrency(stats.youOwe)}</strong>
          <small>Open balances you still need to settle</small>
        </article>
        <article className="card friends-summary-card">
          <span>Friends who owe you</span>
          <strong>{stats.friendsWhoOwe}</strong>
          <small>Friends with a positive balance in your favor</small>
        </article>
      </div>

      <div className="friends-layout">
        <div className="friends-list card">
          <div className="card-header">
            <h2>Friend activity</h2>
            <span className="friends-count">{filteredFriends.length} shown</span>
          </div>

          {loading ? (
            <div className="friends-empty-state">
              <h3>Loading friends</h3>
              <p>Loading your current friends now.</p>
            </div>
          ) : error ? (
            <div className="friends-empty-state">
              <h3>Unable to load friends</h3>
              <p>{error}</p>
            </div>
          ) : filteredFriends.length ? (
            <div className="friends-rows">
              {filteredFriends.map(friend => {
                const status = getFriendStatus(friend.balance)
                const balance = Number(friend.balance || 0)

                return (
                  <article className="friend-row" key={friend.id}>
                    <div className="friend-row-main">
                      <div className="friend-badge">{friend.avatar_emoji || getInitials(friend.display_name)}</div>
                      <div>
                        <div className="friend-row-heading">
                          <h3>{friend.display_name}</h3>
                          <span className={`friend-status friend-status--${status.tone}`}>
                            {status.label}
                          </span>
                        </div>
                        <p className="friend-contact">{friend.email}</p>
                        <p className="friend-note">{status.note}</p>
                        <div className="friend-groups">
                          <span>{formatAddedDate(friend.added_at)}</span>
                          {friend.shared_group_ids?.length > 0
                            ? <span>Shared groups: {friend.shared_group_ids.map(id => groups.find(g => g.id === id)?.name).filter(Boolean).join(', ')}</span>
                            : <span>No shared groups</span>
                          }
                        </div>
                      </div>
                    </div>

                    <div className="friend-row-side">
                      <span className={balance >= 0 ? 'balance-positive' : 'balance-negative'}>
                        {balance >= 0 ? '+' : '-'}{formatCurrency(balance)}
                      </span>
                      <button
                        type="button"
                        className="btn-link friend-remove-btn"
                        onClick={() => handleRemoveFriend(friend.id)}
                        disabled={removingFriendId === friend.id}
                      >
                        {removingFriendId === friend.id ? 'Removing...' : 'Remove'}
                      </button>
                    </div>
                  </article>
                )
              })}
            </div>
          ) : (
            <div className="friends-empty-state">
              <h3>No friends found</h3>
              <p>Add someone from the search panel to start using the friends feature.</p>
            </div>
          )}
        </div>

        <aside className="friends-side">
          <div className="card friend-invite-card">
            <div className="card-header">
              <h2>Add a friend</h2>
            </div>

            <label>
              Search by email
              <input
                type="text"
                value={friendQuery}
                onChange={event => setFriendQuery(event.target.value)}
                placeholder="friend@example.com"
              />
            </label>

            <p className="friend-helper-text">
              Search by email to quickly find people and add them to your friends list.
            </p>

            {searchingUsers ? (
              <div className="friends-search-results">
                <p className="friend-helper-text">Searching users...</p>
              </div>
            ) : searchResults.length ? (
              <div className="friends-search-results">
                {searchResults.map(user => {
                  const alreadyAdded = existingFriendIds.has(user.id)

                  return (
                    <div className="friend-search-row" key={user.id}>
                      <div className="friend-row-main">
                        <div className="friend-badge">{user.avatar_emoji || getInitials(user.display_name)}</div>
                        <div>
                          <h3>{user.display_name}</h3>
                          <p className="friend-contact">{user.email}</p>
                        </div>
                      </div>

                      <button
                        type="button"
                        className="btn-primary friend-search-action"
                        disabled={alreadyAdded || submittingFriendId === user.id}
                        onClick={() => handleAddFriend(user.id)}
                      >
                        {alreadyAdded ? 'Added' : submittingFriendId === user.id ? 'Adding...' : 'Add'}
                      </button>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="friends-search-results friends-search-results--empty">
                <p className="friend-helper-text">
                  {searchFeedback || 'Search for a user by email to add them as a friend.'}
                </p>
              </div>
            )}
          </div>

        </aside>
      </div>
    </section>
  )
}

export default FriendsTab
