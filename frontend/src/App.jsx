import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import './App.css'

function App() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">💰</span>
          <span className="logo-text">DivvyUp</span>
        </div>
        <ul className="nav-links">
          <li
            className={activePage === 'dashboard' ? 'active' : ''}
            onClick={() => setActivePage('dashboard')}
          >
            <span className="nav-icon">🏠</span> Dashboard
          </li>
          <li
            className={activePage === 'transactions' ? 'active' : ''}
            onClick={() => setActivePage('transactions')}
          >
            <span className="nav-icon">💳</span> Transactions
          </li>
          <li
            className={activePage === 'budget' ? 'active' : ''}
            onClick={() => setActivePage('budget')}
          >
            <span className="nav-icon">📊</span> Budget
          </li>
          <li
            className={activePage === 'group' ? 'active' : ''}
            onClick={() => setActivePage('group')}
          >
            <span className="nav-icon">👥</span> Group
          </li>
        </ul>
      </nav>

      <main className="main-content">
        {activePage === 'dashboard' && <Dashboard />}
        {activePage === 'transactions' && <div className="page-placeholder"><h2>Transactions — coming soon</h2></div>}
        {activePage === 'budget' && <div className="page-placeholder"><h2>Budget — coming soon</h2></div>}
        {activePage === 'group' && <div className="page-placeholder"><h2>Group — coming soon</h2></div>}
      </main>
    </div>
  )
}

export default App
