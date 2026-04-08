import { useState, useEffect } from 'react'
import SummaryCard from '../components/SummaryCard'
import TransactionList from '../components/TransactionList'
import BudgetCategories from '../components/BudgetCategories'
import GroupMembers from '../components/GroupMembers'
import { getExpenses, getGroupBalances, getGroupMembers, createExpense } from '../api'
import './Dashboard.css'

function Dashboard({ groups = [] }) {
  const [selectedGroup, setSelectedGroup] = useState(null)
  const [expenses, setExpenses] = useState([])
  const [balances, setBalances] = useState([])
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (groups.length > 0 && !selectedGroup) {
      setSelectedGroup(groups[0])
    }
  }, [groups, selectedGroup])

  useEffect(() => {
    if (selectedGroup) {
      loadGroupData(selectedGroup.id)
    } else {
      setExpenses([])
      setBalances([])
      setMembers([])
    }
  }, [selectedGroup])

  async function loadGroupData(groupId) {
    setLoading(true)
    try {
      const [expData, balData, memData] = await Promise.all([
        getExpenses(groupId),
        getGroupBalances(groupId),
        getGroupMembers(groupId),
      ])
      setExpenses(expData)
      setBalances(balData)
      setMembers(memData)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddTransaction() {
    if (!selectedGroup) {
      alert('Please create and select a group first.')
      return
    }

    const description = prompt('Enter expense description:')
    if (!description) return

    const amount = parseFloat(prompt('Enter amount:'))
    if (Number.isNaN(amount)) return

    try {
      await createExpense(selectedGroup.id, {
        description,
        amount,
        base_amount: amount,
        currency: 'USD',
        expense_date: new Date().toISOString().split('T')[0],
        category_id: 1,
        split_type: 'equal',
      })
      loadGroupData(selectedGroup.id)
    } catch (err) {
      alert('Failed to add expense: ' + err.message)
    }
  }

  if (!groups.length) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <div>
            <h1>Dashboard</h1>
            <p className="dashboard-date">February 2026</p>
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
  }))

  const mockBudgets = [
    { category: 'Food', spent: 121.82, limit: 300 },
    { category: 'Entertainment', spent: 15.99, limit: 50 },
    { category: 'Transport', spent: 52.10, limit: 150 },
    { category: 'Shopping', spent: 0, limit: 200 },
  ]

  const transformedMembers = members.map(mem => ({
    id: mem.user_id,
    name: mem.display_name || 'Member',
    initials: (mem.display_name || 'M').split(' ').map(n => n[0]).join('').toUpperCase(),
    owes: balances.find(b => b.user_id === mem.user_id)?.net_balance || 0,
    isYou: false,
  }))

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>{selectedGroup?.name || 'Dashboard'}</h1>
          <p className="dashboard-date">February 2026</p>
        </div>
        <button className="btn-primary" onClick={handleAddTransaction}>+ Add Transaction</button>
      </div>

      <div className="group-selector">
        <select
          value={selectedGroup?.id || ''}
          onChange={e => setSelectedGroup(groups.find(g => g.id === e.target.value))}
        >
          {groups.map(g => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      <div className="summary-cards">
        <SummaryCard title="Total Balance" amount={2841.09} type="balance" />
        <SummaryCard title="Monthly Income" amount={1200.00} type="income" />
        <SummaryCard title="Monthly Expenses" amount={189.91} type="expense" />
        <SummaryCard title="Group Owes You" amount={33.25} type="owed" />
      </div>

      <div className="dashboard-grid">
        <div className="grid-left">
          <TransactionList transactions={transactions} />
        </div>
        <div className="grid-right">
          <BudgetCategories budgets={mockBudgets} />
          <GroupMembers members={transformedMembers} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard