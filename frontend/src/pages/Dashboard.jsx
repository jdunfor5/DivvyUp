import { useState, useEffect, useMemo } from 'react'
import SummaryCard from '../components/SummaryCard'
import TransactionList from '../components/TransactionList'
import GroupMembers from '../components/GroupMembers'
import Settlements from '../components/Settlements'
import ExpenseForm from '../components/ExpenseForm'
import SettlementForm from '../components/SettlementForm'
import RecurringExpenses from '../components/RecurringExpenses'
import RecurringExpenseForm from '../components/RecurringExpenseForm'
import BudgetCategories from '../components/BudgetCategories'
import { getExpenses, getGroupBalances, getGroupMembers, createExpense, updateExpense, deleteExpense, getCurrentUser, getSettlements, createSettlement, confirmSettlement, cancelSettlement, removeMember, transferAdmin, leaveGroup, getCategories, getRecurringExpenses, createRecurringExpense, updateRecurringExpense, deactivateRecurringExpense } from '../api'
import './Dashboard.css'

function Dashboard({ groups = [], selectedGroupId, onSelectGroup }) {
  const [expenses, setExpenses] = useState([])
  const [balances, setBalances] = useState([])
  const [members, setMembers] = useState([])
  const [settlements, setSettlements] = useState([])
  const [currentUser, setCurrentUser] = useState(null)
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showExpenseForm, setShowExpenseForm] = useState(false)
  const [editingExpense, setEditingExpense] = useState(null)
  const [showRecurringForm, setShowRecurringForm] = useState(false)
  const [editingRecurring, setEditingRecurring] = useState(null)
  const [recurringExpenses, setRecurringExpenses] = useState([])
  const [settlementTarget, setSettlementTarget] = useState(null)

  const selectedGroup = useMemo(() => {
    if (!groups.length) return null
    return groups.find(g => g.id === selectedGroupId) || groups[0]
  }, [groups, selectedGroupId])

  useEffect(() => {
    getCurrentUser().then(setCurrentUser).catch(console.error)
    getCategories().then(setCategories).catch(console.error)
  }, [])

  useEffect(() => {
    if (selectedGroup) {
      loadGroupData(selectedGroup.id)
    } else {
      setExpenses([])
      setBalances([])
      setMembers([])
      setSettlements([])
    }
  }, [selectedGroup])

  async function loadGroupData(groupId) {
    setLoading(true)
    try {
      const [expData, balData, memData, setData, recData] = await Promise.all([
        getExpenses(groupId),
        getGroupBalances(groupId),
        getGroupMembers(groupId),
        getSettlements(groupId),
        getRecurringExpenses(groupId),
      ])
      setExpenses(expData)
      setBalances(balData)
      setMembers(memData)
      setSettlements(setData)
      setRecurringExpenses(recData)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleAddTransaction() {
    if (!selectedGroup) {
      alert('Please create and select a group first.')
      return
    }
    setShowExpenseForm(true)
  }

  function handleEditExpense(expenseId) {
    const raw = expenses.find(e => e.id === expenseId)
    if (raw) setEditingExpense(raw)
  }

  async function handleExpenseSubmit(body) {
    await createExpense(selectedGroup.id, body)
    loadGroupData(selectedGroup.id)
  }

  async function handleEditExpenseSubmit(body) {
    await updateExpense(selectedGroup.id, editingExpense.id, body)
    setEditingExpense(null)
    loadGroupData(selectedGroup.id)
  }

  async function handleDeleteExpense(expenseId) {
    if (!confirm('Delete this transaction?')) return
    try {
      await deleteExpense(selectedGroup.id, expenseId)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to delete: ' + err.message)
    }
  }

  async function handleRecurringSubmit(body) {
    await createRecurringExpense(selectedGroup.id, body)
    loadGroupData(selectedGroup.id)
  }

  async function handleEditRecurringSubmit(body) {
    await updateRecurringExpense(selectedGroup.id, editingRecurring.id, body)
    setEditingRecurring(null)
    loadGroupData(selectedGroup.id)
  }

  async function handleDeactivateRecurring(recurringId) {
    if (!confirm('Deactivate this recurring expense?')) return
    try {
      await deactivateRecurringExpense(selectedGroup.id, recurringId)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to deactivate: ' + err.message)
    }
  }

  function handleSettlePayment(member) {
    if (!selectedGroup) return
    setSettlementTarget(member)
  }

  async function handleSettlementSubmit(data) {
    await createSettlement(selectedGroup.id, settlementTarget.id, data)
    setSettlementTarget(null)
    loadGroupData(selectedGroup.id)
  }

  async function handleConfirmSettlement(settlementId) {
    if (!selectedGroup) return
    try {
      await confirmSettlement(selectedGroup.id, settlementId)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to confirm settlement: ' + err.message)
    }
  }

  async function handleCancelSettlement(settlementId) {
    if (!selectedGroup) return
    if (!confirm('Are you sure you want to cancel this settlement?')) return
    try {
      await cancelSettlement(selectedGroup.id, settlementId)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to cancel settlement: ' + err.message)
    }
  }

  async function handleRemoveMember(userId) {
    if (!selectedGroup) return
    if (!confirm('Remove this member from the group?')) return
    try {
      await removeMember(selectedGroup.id, userId)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to remove member: ' + err.message)
    }
  }

  async function handleTransferAdmin(userId) {
    if (!selectedGroup) return
    if (!confirm('Transfer admin to this member? You will become a regular member')) return
    try {
      await transferAdmin(selectedGroup.id, userId)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to transfer admin: ' + err.message)
    }
  }

  async function handleLeaveGroup() {
    if (!selectedGroup) return
    if (!confirm('Are you sure you want to leave this group?')) return
    try {
      await leaveGroup(selectedGroup.id)
      onSelectGroup(null)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      if (err.message.includes('Admin')) {
        alert('Failed to leave group: there needs to be an admin in the group. Transfer admin to someone else first.')
      } else {
        alert('Failed to leave group: ' + err.message)
      }
    }
  }

  const categorySpending = useMemo(() => {
    const map = {}
    for (const exp of expenses) {
      const cat = categories.find(c => c.id === exp.category_id)
      const key = cat?.name || 'Misc'
      if (!map[key]) map[key] = { category: key, icon: cat?.icon || '', spent: 0 }
      map[key].spent += Number(exp.amount)
    }
    return Object.values(map).sort((a, b) => b.spent - a.spent)
  }, [expenses, categories])

  const currentMonthName = new Date().toLocaleString('default', { month: 'long', year: 'numeric' })

  if (!groups.length) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <div>
            <h1>Dashboard</h1>
            <p className="dashboard-date"><span id="display-month">{currentMonthName}</span></p>
          </div>
        </div>
        <div>Please create a group first from the sidebar.</div>
      </div>
    )
  }

  if (loading) return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>Loading...</p>
    </div>
  )
  if (error) return <div>Error: {error}</div>

  const transactions = expenses
    .map(exp => ({
      id: exp.id,
      description: exp.description,
      amount: Number(exp.amount) * -1,
      date: new Date(exp.expense_date).toISOString().split('T')[0],
      category: categories.find(c => c.id === exp.category_id)?.name || 'Misc',
      paidByName: exp.paid_by_name || null,
    }))
    .sort((a, b) => new Date(b.date) - new Date(a.date))

  const transformedMembers = members.map(mem => {
    const balance = balances.find(b => b.user_id === mem.user_id)?.net_balance || 0
    const paymentsToYou = settlements
      .filter(s => s.payer_id === mem.user_id && s.payee_id === currentUser?.id && s.status === 'completed')
      .reduce((sum, s) => sum + Number(s.amount), 0)
    const paymentsFromYou = settlements
      .filter(s => s.payer_id === currentUser?.id && s.payee_id === mem.user_id && s.status === 'completed')
      .reduce((sum, s) => sum + Number(s.amount), 0)

    const isYou = mem.user_id === currentUser?.id
    const isAdmin = mem.role === 'admin'
    const displayName = isYou ? `${mem.display_name} (You)` : (mem.display_name || 'Friend')
    const initialsSource = mem.display_name || 'You'

    return {
      id: mem.user_id,
      name: displayName,
      initials: initialsSource.split(' ').map(n => n[0]).join('').toUpperCase(),
      avatar: mem.avatar_emoji,
      owes: Number(balance),
      paymentsToYou,
      paymentsFromYou,
      canSettle: Number(balance) > 0,
      isYou,
      isAdmin,
    }
  })

  transformedMembers.sort((a, b) => {
    if (a.isAdmin !== b.isAdmin) return a.isAdmin ? -1 : 1
    return a.name.localeCompare(b.name)
  })

  const currentUserIsAdmin = members.find(m => m.user_id === currentUser?.id)?.role === 'admin'

  const currentMonth = new Date().getMonth()
  const currentYear = new Date().getFullYear()

  const monthlyExpenses = expenses
    .filter(exp => {
      const expDate = new Date(exp.expense_date)
      return expDate.getMonth() === currentMonth && expDate.getFullYear() === currentYear
    })
    .reduce((sum, exp) => sum + Number(exp.amount), 0)

  const userBalance = Math.max(0, balances.reduce((sum, b) => sum + Number(b.net_balance), 0))
  const groupOwesYou = balances.reduce((sum, b) => sum + Math.max(0, -Number(b.net_balance)), 0)

  const todayStr = new Date().toLocaleDateString('en-CA')
  const in30DaysStr = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString('en-CA')
  const upcomingTotal = recurringExpenses
    .filter(r => r.is_active && r.next_due_date >= todayStr && r.next_due_date <= in30DaysStr)
    .reduce((sum, r) => sum + Number(r.amount), 0)

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>{selectedGroup?.name || 'Dashboard'}</h1>
          <p className="dashboard-date"><span id="display-month">{currentMonthName}</span></p>
        </div>
        <div className="header-actions">
          <button className="btn-primary" onClick={() => setShowRecurringForm(true)}>+ Add Recurring</button>
          <button className="btn-primary" onClick={handleAddTransaction}>+ Add Expenses</button>
        </div>
      </div>

      <div className="summary-cards">
        <SummaryCard title="Monthly Expenses" amount={monthlyExpenses} type="expense" />
        <SummaryCard title="Your Balance" amount={Number(userBalance)} type="balance" />
        <SummaryCard title="Upcoming (30 days)" amount={upcomingTotal} type="upcoming" />
        <SummaryCard title="Group Owes You" amount={groupOwesYou} type="owed" />
      </div>

      <div className="dashboard-grid">
        <div className="grid-left">
          <TransactionList
            transactions={transactions}
            groupId={selectedGroup?.id}
            currentUserId={currentUser?.id}
            groupMembers={members}
            onEdit={handleEditExpense}
            onDelete={handleDeleteExpense}
          />
        </div>
        <div className="grid-right">
          <BudgetCategories budgets={categorySpending} />
          <RecurringExpenses
            recurringExpenses={recurringExpenses}
            categories={categories}
            onDeactivate={handleDeactivateRecurring}
            onEdit={setEditingRecurring}
          />
        </div>
        <div className="grid-recurring">
          <GroupMembers
            members={transformedMembers}
            currentUser={currentUser}
            isAdmin={currentUserIsAdmin}
            onSettlePayment={handleSettlePayment}
            onRemoveMember={handleRemoveMember}
            onTransferAdmin={handleTransferAdmin}
            onLeaveGroup={handleLeaveGroup}
          />
          <Settlements
            settlements={settlements}
            currentUserId={currentUser?.id}
            members={members}
            onConfirmSettlement={handleConfirmSettlement}
            onCancelSettlement={handleCancelSettlement}
          />
        </div>
      </div>

      {showExpenseForm && (
        <ExpenseForm
          members={members}
          currentUserId={currentUser?.id}
          categories={categories}
          onSubmit={handleExpenseSubmit}
          onClose={() => setShowExpenseForm(false)}
        />
      )}

      {editingExpense && (
        <ExpenseForm
          members={members}
          currentUserId={currentUser?.id}
          categories={categories}
          initialValues={editingExpense}
          onSubmit={handleEditExpenseSubmit}
          onClose={() => setEditingExpense(null)}
        />
      )}

      {showRecurringForm && (
        <RecurringExpenseForm
          categories={categories}
          onSubmit={handleRecurringSubmit}
          onClose={() => setShowRecurringForm(false)}
        />
      )}

      {editingRecurring && (
        <RecurringExpenseForm
          categories={categories}
          initialValues={editingRecurring}
          onSubmit={handleEditRecurringSubmit}
          onClose={() => setEditingRecurring(null)}
        />
      )}

      {settlementTarget && (
        <SettlementForm
          payee={settlementTarget}
          maxAmount={settlementTarget.owes}
          onSubmit={handleSettlementSubmit}
          onClose={() => setSettlementTarget(null)}
        />
      )}
    </div>
  )
}

export default Dashboard