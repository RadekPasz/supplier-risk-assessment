import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createSupplier, fetchRiskSummary } from '../api'
import type { Supplier, SupplierStatus, SupplierTier } from '../types'

const tierClass: Record<SupplierTier, string> = {
  critical: 'badge critical',
  high: 'badge high',
  medium: 'badge medium',
  low: 'badge low',
}

export default function SupplierList() {
  const [rows, setRows] = useState<Supplier[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [tier, setTier] = useState<SupplierTier>('medium')
  const [status, setStatus] = useState<SupplierStatus>('pending')

  const load = () => {
    setLoading(true)
    fetchRiskSummary()
      .then(setRows)
      .catch((e: Error) => setErr(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr(null)
    try {
      await createSupplier({ name, tier, status, description: null, website: null })
      setName('')
      setShowForm(false)
      load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to create')
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Suppliers</h1>
          <p className="muted">Sorted by risk score (highest first)</p>
        </div>
        <button type="button" className="btn primary" onClick={() => setShowForm((s) => !s)}>
          {showForm ? 'Cancel' : 'Add supplier'}
        </button>
      </header>

      {showForm && (
        <form className="card form-inline" onSubmit={onCreate}>
          <input
            required
            placeholder="Supplier name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <select value={tier} onChange={(e) => setTier(e.target.value as SupplierTier)}>
            <option value="critical">critical</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value as SupplierStatus)}>
            <option value="pending">pending</option>
            <option value="active">active</option>
            <option value="archived">archived</option>
          </select>
          <button className="btn primary" type="submit">
            Create
          </button>
        </form>
      )}

      {err && <div className="alert error">{err}</div>}
      {loading && <p className="muted">Loading…</p>}

      {!loading && (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Tier</th>
                <th>Risk</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.id}>
                  <td>
                    <strong>{s.name}</strong>
                  </td>
                  <td>
                    <span className={tierClass[s.tier]}>{s.tier}</span>
                  </td>
                  <td>{s.risk_score.toFixed(1)}</td>
                  <td>{s.status}</td>
                  <td>
                    <Link className="link" to={`/suppliers/${s.id}`}>
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="muted">No suppliers yet.</p>}
        </div>
      )}
    </div>
  )
}
