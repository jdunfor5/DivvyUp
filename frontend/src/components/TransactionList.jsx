import { useEffect, useState } from 'react'
import { getExpenseComments, createExpenseComment } from '../api'
import './TransactionList.css'

const PAGE_SIZE = 5

const SPLIT_LABELS = {
  equal: 'Equal split',
  exact: 'Exact split',
  percentage: '% split',
}

function TransactionList({ transactions, groupId, currentUserId, groupMembers, onEdit, onDelete }) {
  const [commentsByExpense, setCommentsByExpense] = useState({})
  const [drafts, setDrafts] = useState({})
  const [openExpenseId, setOpenExpenseId] = useState(null)
  const [loadingComment, setLoadingComment] = useState(false)
  const [showAll, setShowAll] = useState(false)

  const visible = showAll ? transactions : transactions.slice(0, PAGE_SIZE)

  const memberNames = groupMembers?.reduce((map, member) => {
    map[member.user_id] = member.display_name || member.email || 'Member'
    return map
  }, {}) || {}

  const visibleIds = visible.map(tx => tx.id).join(',')

  useEffect(() => {
    if (!groupId || !visibleIds) return
    let cancelled = false
    const load = async () => {
      const toFetch = visible.filter(tx => commentsByExpense[tx.id] === undefined)
      if (!toFetch.length) return
      const newComments = {}
      await Promise.all(toFetch.map(async (tx) => {
        try {
          const comments = await getExpenseComments(groupId, tx.id)
          if (!cancelled) newComments[tx.id] = comments
        } catch {
          if (!cancelled) newComments[tx.id] = []
        }
      }))
      if (!cancelled) setCommentsByExpense(current => ({ ...current, ...newComments }))
    }
    load()
    return () => { cancelled = true }
  }, [groupId, visibleIds])

  async function loadComments(expenseId) {
    if (commentsByExpense[expenseId] !== undefined) return
    try {
      const comments = await getExpenseComments(groupId, expenseId)
      setCommentsByExpense(current => ({ ...current, [expenseId]: comments }))
    } catch {
      setCommentsByExpense(current => ({ ...current, [expenseId]: [] }))
    }
  }

  const handleDraftChange = (expenseId, value) => {
    setDrafts(current => ({ ...current, [expenseId]: value }))
  }

  const handleCreateComment = async (expenseId) => {
    const body = (drafts[expenseId] || '').trim()
    if (!body) return

    setLoadingComment(true)
    try {
      await createExpenseComment(groupId, expenseId, body)
      const updated = await getExpenseComments(groupId, expenseId)
      setCommentsByExpense(current => ({ ...current, [expenseId]: updated }))
      setDrafts(current => ({ ...current, [expenseId]: '' }))
    } catch (err) {
      console.error('Failed to post comment', err)
    } finally {
      setLoadingComment(false)
    }
  }

  return (
    <div className="transaction-list card">
      <div className="card-header">
        <h2>Recent Expenses</h2>
        {transactions.length > PAGE_SIZE && (
          <button className="btn-link" onClick={() => setShowAll(v => !v)}>
            {showAll ? 'Show less' : `View all (${transactions.length})`}
          </button>
        )}
      </div>
      <ul>
        {visible.map((tx) => (
          <li key={tx.id} className="transaction-item">
            <div className="transaction-main-row">
              <div className="transaction-left">
                <div className="transaction-category-dot" data-category={tx.category} />
                <div style={{ minWidth: 0 }}>
                  <p className="transaction-desc">{tx.description}</p>
                  <p className="transaction-date">
                    {tx.date} · {tx.category}{tx.paidByName ? ` · Paid by ${tx.paidByName}` : ''}{tx.splitType ? ` · ${SPLIT_LABELS[tx.splitType] || tx.splitType}` : ''}
                  </p>
                </div>
              </div>
              <p className={`transaction-amount ${tx.amount < 0 ? 'negative' : 'positive'}`}>
                {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount).toFixed(2)}
              </p>
            </div>
            <div className="transaction-actions">
              <button
                className={`btn-comment-toggle${openExpenseId === tx.id ? ' open' : ''}`}
                onClick={() => {
                  const next = openExpenseId === tx.id ? null : tx.id
                  setOpenExpenseId(next)
                  if (next) loadComments(next)
                }}
              >
                🗨 {((commentsByExpense[tx.id] || []).length)}
              </button>
              {onEdit && (
                <button
                  className="btn-edit"
                  onClick={() => onEdit(tx.id)}
                  title="Edit"
                >
                  ✎
                </button>
              )}
              {onDelete && (
                <button
                  className="btn-delete"
                  onClick={() => onDelete(tx.id)}
                  title="Delete"
                >
                  ✕
                </button>
              )}
            </div>
            {openExpenseId === tx.id && (
              <div className="expense-comment-panel">
                <div className="comment-list">
                  {(commentsByExpense[tx.id] || []).map(comment => (
                    <div key={comment.id} className="comment-row">
                      <div className="comment-meta">
                        <span className="comment-sender">
                          {comment.user_id === currentUserId ? 'You' : memberNames[comment.user_id] || 'Member'}
                        </span>
                        <span className="comment-date">{new Date(comment.created_at).toLocaleString()}</span>
                      </div>
                      <p className="comment-body">{comment.body}</p>
                    </div>
                  ))}
                </div>
                <textarea
                  className="comment-input"
                  placeholder="Write a comment..."
                  value={drafts[tx.id] || ''}
                  onChange={e => handleDraftChange(tx.id, e.target.value)}
                />
                <button
                  className="btn-primary btn-comment-submit"
                  onClick={() => handleCreateComment(tx.id)}
                  disabled={loadingComment || !(drafts[tx.id] || '').trim()}
                >
                  Post comment
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default TransactionList
