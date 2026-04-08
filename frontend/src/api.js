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
  const res = await fetch(`${BASE_URL}/users/me`, {
    headers: authHeaders(),
  })
  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json()
}

// Generic authenticated request helper
export async function api(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

// ── Groups ───────────────────────────────────────────────────

export async function getGroups() {
  return api('/groups/')
}

export async function createGroup(data) {
  return api('/groups/', { method: 'POST', body: JSON.stringify(data) })
}

export async function getGroup(groupId) {
  return api(`/groups/${groupId}`)
}

export async function getGroupBalances(groupId) {
  return api(`/groups/${groupId}/balances`)
}

export async function getGroupMembers(groupId) {
  return api(`/groups/${groupId}/members`)
}

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
