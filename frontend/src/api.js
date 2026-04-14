const BASE_URL = 'http://127.0.0.1:8000'

export function getToken() {
  return localStorage.getItem('token')
}

function saveToken(token) {
  localStorage.setItem('token', token)
}

export function clearToken() {
  localStorage.removeItem('token')
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Login — OAuth2 requires form-encoded body with "username" field
export async function login(email, password) {
  const body = new URLSearchParams({ username: email, password })
  const res = await fetch(`${BASE_URL}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'Login failed')
  }
  const data = await res.json()
  saveToken(data.access_token)
}

export async function getCurrentUser() {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
  
  try {
    const res = await fetch(`${BASE_URL}/users/me`, {
      headers: authHeaders(),
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    if (!res.ok) throw new Error('Failed to fetch user')
    return res.json()
  } catch (err) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      throw new Error('Request timeout')
    }
    throw err
  }
}

// Generic authenticated request helper
export async function api(path, options = {}) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
  
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
        ...options.headers,
      },
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      const detail = Array.isArray(err.detail)
        ? err.detail.map(e => e.msg).join(', ')
        : err.detail
      throw new Error(detail || `Request failed: ${res.status}`)
    }
    if (res.status === 204) return null
    return res.json()
  } catch (err) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError') {
      throw new Error('Request timeout')
    }
    throw err
  }
}

// ── Groups ───────────────────────────────────────────────────

export async function getGroups() {
  return api('/groups/')
}

export async function createGroup(data) {
  return api('/groups/', { method: 'POST', body: JSON.stringify(data) })
}

export async function deleteGroup(groupId) {
  return api(`/groups/${groupId}`, { method: 'DELETE' })
}

export async function getGroupBalances(groupId) {
  return api(`/groups/${groupId}/balances`)
}

export async function getGroupMembers(groupId) {
  return api(`/groups/${groupId}/members`)
}

export async function getExpenseComments(groupId, expenseId) {
  return api(`/groups/${groupId}/expenses/${expenseId}/comments/`)
}

export async function createExpenseComment(groupId, expenseId, body) {
  return api(`/groups/${groupId}/expenses/${expenseId}/comments/`, {
    method: 'POST',
    body: JSON.stringify({ body }),
  })
}

export async function joinGroup(inviteCode) {
  return api('/groups/join', { method: 'POST', body: JSON.stringify({ invite_code: inviteCode }) })
}

// ── Settlements ──────────────────────────────────────────────

// ── Expenses ─────────────────────────────────────────────────

export async function getExpenses(groupId) {
  return api(`/groups/${groupId}/expenses/`)
}

export async function createExpense(groupId, data) {
  return api(`/groups/${groupId}/expenses/`, { method: 'POST', body: JSON.stringify(data) })
}

export async function updateExpense(groupId, expenseId, data) {
  return api(`/groups/${groupId}/expenses/${expenseId}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export async function deleteExpense(groupId, expenseId) {
  return api(`/groups/${groupId}/expenses/${expenseId}`, { method: 'DELETE' })
}

// ── Settlements ──────────────────────────────────────────────

export async function getSettlements(groupId) {
  return api(`/groups/${groupId}/settlements/`)
}

export async function createSettlement(groupId, payeeId, data) {
  return api(`/groups/${groupId}/settlements/${payeeId}`, { method: 'POST', body: JSON.stringify(data) })
}

export async function confirmSettlement(groupId, settlementId) {
  return api(`/groups/${groupId}/settlements/${settlementId}/confirm`, { method: 'PATCH' })
}

export async function cancelSettlement(groupId, settlementId) {
  return api(`/groups/${groupId}/settlements/${settlementId}/cancel`, { method: 'PATCH' })
}

// ── Group Management ──────────────────────────────────────────────

export async function removeMember(groupId, userId){
  return api(`/groups/${groupId}/members/${userId}`, { method: 'DELETE'})
}

export async function transferAdmin(groupId, userId){
  return api(`/groups/${groupId}/members/${userId}/transfer`, { method: 'PATCH'})
}

export async function leaveGroup(groupId){
  return api(`/groups/${groupId}/members`, { method: 'DELETE'})
}

// Categories
export async function getCategories() {
  return api('/categories/')
}