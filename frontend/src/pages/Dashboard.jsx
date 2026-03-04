import SummaryCard from '../components/SummaryCard'
import TransactionList from '../components/TransactionList'
import BudgetCategories from '../components/BudgetCategories'
import GroupMembers from '../components/GroupMembers'
import './Dashboard.css'

const mockTransactions = [
  { id: 1, description: 'Grocery Store', amount: -84.32, date: '2026-02-25', category: 'Food' },
  { id: 2, description: 'Netflix', amount: -15.99, date: '2026-02-24', category: 'Entertainment' },
  { id: 3, description: 'Paycheck', amount: 1200.00, date: '2026-02-23', category: 'Income' },
  { id: 4, description: 'Gas Station', amount: -52.10, date: '2026-02-22', category: 'Transport' },
  { id: 5, description: 'Restaurant', amount: -37.50, date: '2026-02-21', category: 'Food' },
]

const mockBudgets = [
  { category: 'Food', spent: 121.82, limit: 300 },
  { category: 'Entertainment', spent: 15.99, limit: 50 },
  { category: 'Transport', spent: 52.10, limit: 150 },
  { category: 'Shopping', spent: 0, limit: 200 },
]

const mockMembers = [
  { id: 1, name: 'Lando', initials: 'LA', owes: 0, isYou: true },
  { id: 2, name: 'Alex', initials: 'AX', owes: 24.50 },
  { id: 3, name: 'Jordan', initials: 'JO', owes: -12.00 },
  { id: 4, name: 'Casey', initials: 'CA', owes: 8.75 },
]

function Dashboard() {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p className="dashboard-date">February 2026</p>
        </div>
        <button className="btn-primary">+ Add Transaction</button>
      </div>

      <div className="summary-cards">
        <SummaryCard title="Total Balance" amount={2841.09} type="balance" />
        <SummaryCard title="Monthly Income" amount={1200.00} type="income" />
        <SummaryCard title="Monthly Expenses" amount={189.91} type="expense" />
        <SummaryCard title="Group Owes You" amount={33.25} type="owed" />
      </div>

      <div className="dashboard-grid">
        <div className="grid-left">
          <TransactionList transactions={mockTransactions} />
        </div>
        <div className="grid-right">
          <BudgetCategories budgets={mockBudgets} />
          <GroupMembers members={mockMembers} />
        </div>
      </div>
    </div>
  )
}

export default Dashboard