import { useEffect, useState } from 'react'
import { getExpenseComments, createExpenseComment } from '../api'
import './TransactionList.css'

function TransactionList({ transactions, groupId, currentUserId, groupMembers }) {
  const [commentsByExpense, setCommentsByExpense] = useState({})
  const [drafts, setDrafts] = useState({})
  const [openExpenseId, setOpenExpenseId] = useState(null)
  const [loadingComment, setLoadingComment] = useState(false)

  const memberNames = groupMembers?.reduce((map, member) => {
    map[member.user_id] = member.display_name || member.email || 'Member'
    return map
  }, {}) || {}

  useEffect(() => {
    if (!groupId || transactions.length === 0) return

    let cancelled = false
    const loadAllComments = async () => {
      const newComments = {}
      await Promise.all(transactions.map(async (tx) => {
        try {
          const comments = await getExpenseComments(groupId, tx.id)
          if (!cancelled) newComments[tx.id] = comments
        } catch (err) {
          if (!cancelled) newComments[tx.id] = []
        }
      }))
      if (!cancelled) setCommentsByExpense(newComments)
    }

    loadAllComments()
    return () => { cancelled = true }
  }, [groupId, transactions])

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
        <h2>Recent Transactions</h2>
        <button className="btn-link">View all</button>
      </div>
      <ul>
        {transactions.map((tx) => (
          <li key={tx.id} className="transaction-item">
            <div className="transaction-left">
              <div className="transaction-category-dot" data-category={tx.category} />
              <div>
                <p className="transaction-desc">{tx.description}</p>
                <p className="transaction-date">
                  {tx.date} · {tx.category}{tx.paidByName ? ` · Paid by ${tx.paidByName}` : ''}
                </p>
                <div className="transaction-actions">
                  <button
                    className="btn-comment-toggle"
                    onClick={() => setOpenExpenseId(openExpenseId === tx.id ? null : tx.id)}
                  >
                    💬 {((commentsByExpense[tx.id] || []).length)}
                  </button>
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
              </div>
            </div>
            <p className={`transaction-amount ${tx.amount < 0 ? 'negative' : 'positive'}`}>
              {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount).toFixed(2)}
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default TransactionList