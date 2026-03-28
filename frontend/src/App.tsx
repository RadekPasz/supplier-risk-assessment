import { Link, Navigate, Route, Routes } from 'react-router-dom'
import SupplierDetail from './pages/SupplierDetail'
import SupplierList from './pages/SupplierList'
import './index.css'

export default function App() {
  return (
    <div className="app">
      <nav className="nav">
        <Link className="brand" to="/">
          Supplier risk
        </Link>
        <span className="muted small">NIS2 due diligence prototype</span>
      </nav>
      <main className="main">
        <Routes>
          <Route path="/" element={<SupplierList />} />
          <Route path="/suppliers/:id" element={<SupplierDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
