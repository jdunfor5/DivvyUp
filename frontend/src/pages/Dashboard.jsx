import { useState, useEffect, useMemo } from 'react'
import SummaryCard from '../components/SummaryCard'
import TransactionList from '../components/TransactionList'
import GroupMembers from '../components/GroupMembers'
import Settlements from '../components/Settlements'
import ExpenseForm from '../components/ExpenseForm'
import { getExpenses, getGroupBalances, getGroupMembers, createExpense, getCurrentUser, getSettlements, createSettlement, confirmSettlement, cancelSettlement, removeMember, transferAdmin, leaveGroup, getCategories } from '../api'
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
      const [expData, balData, memData, setData] = await Promise.all([
        getExpenses(groupId),
        getGroupBalances(groupId),
        getGroupMembers(groupId),
        getSettlements(groupId),
      ])
      setExpenses(expData)
      setBalances(balData)
      setMembers(memData)
      setSettlements(setData)
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

  async function handleExpenseSubmit(body) {
    await createExpense(selectedGroup.id, body)
    loadGroupData(selectedGroup.id)
  }

  async function handleSettlePayment(member) {
    if (!selectedGroup) return

    if (member.owes <= 0) {
      alert('This member owes you money. Ask them to record the payment from their account, then confirm it in Settlements.')
      return
    }

    const maxAmount = Math.abs(member.owes)
    const amount = parseFloat(prompt(`Enter payment amount (max: $${maxAmount.toFixed(2)}):`))
    
    if (Number.isNaN(amount) || amount <= 0) return
    if (amount > maxAmount) {
      alert(`Amount cannot exceed $${maxAmount.toFixed(2)}`)
      return
    }

    const provider = prompt('Payment method (cash, venmo, paypal, other):') || 'cash'
    const note = prompt('Optional note:') || null

    try {
      await createSettlement(selectedGroup.id, member.id, {
        amount,
        currency: 'USD',
        provider,
        note,
      })
      alert('Payment recorded! The recipient will need to confirm it.')
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to record payment: ' + err.message)
    }
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
      setSelectedGroup(null)
      loadGroupData(selectedGroup.id)
    } catch (err) {
      if (err.message.includes('Admin')) {
        alert('Failed to leave group: there needs to be an admin in the group. Transfer admin to someone else first.')
      } else {
        alert('Failed to leave group: ' + err.message)
      }
    }
  }

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

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>

  const transactions = expenses.map(exp => ({
    id: exp.id,
    description: exp.description,
    amount: Number(exp.amount) * -1,
    date: new Date(exp.expense_date).toISOString().split('T')[0],
    category: 'Misc',
    paidByName: exp.paid_by_name || null,
  }))

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
    const displayName = isYou ? 'You' : (mem.display_name || 'Friend')
    const initialsSource = isYou ? 'You' : (mem.display_name || 'Friend')

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

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ]
  const currentMonthName = monthNames[new Date().getMonth()]

  const currentUserIsAdmin = members.find(m => m.user_id === currentUser?.id)?.role === 'admin'

  const currentMonth = new Date().getMonth()
  const currentYear = new Date().getFullYear()

  const monthlyExpenses = expenses
    .filter(exp => {
      const expDate = new Date(exp.expense_date)
      return expDate.getMonth() === currentMonth && expDate.getFullYear() === currentYear
    })
    .reduce((sum, exp) => sum + Number(exp.amount), 0)

  const userBalance = balances.reduce((sum, b) => sum - Number(b.net_balance), 0)
  const groupOwesYou = balances.reduce((sum, b) => sum + Math.max(0, -Number(b.net_balance)), 0)

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>{selectedGroup?.name || 'Dashboard'}</h1>
          <p className="dashboard-date"><span id="display-month">{currentMonthName}</span></p>
        </div>
        <button className="btn-primary" onClick={handleAddTransaction}>+ Add Transaction</button>
      </div>

      <div className="summary-cards">
        <SummaryCard title="Your Balance" amount={Number(userBalance)} type="balance" />
        <SummaryCard title="Monthly Expenses" amount={monthlyExpenses} type="expense" />
        <SummaryCard title="Group Owes You" amount={groupOwesYou} type="owed" />
      </div>

      <div className="dashboard-grid">
        <div className="grid-left">
          <TransactionList transactions={transactions} groupId={selectedGroup?.id} currentUserId={currentUser?.id} groupMembers={members} />
        </div>
        <div className="grid-right">
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
    </div>
  )
}

export default Dashboard