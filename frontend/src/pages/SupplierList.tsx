import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createSupplier, deleteSupplier, fetchRiskSummary, updateSupplier } from '../api'
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
  const [showForm, setShowForm] = useState(true)
  const [name, setName] = useState('')
  const [tier, setTier] = useState<SupplierTier | ''>('')
  const [status, setStatus] = useState<SupplierStatus | ''>('')
  const [editing, setEditing] = useState<Supplier | null>(null)
  const [editName, setEditName] = useState('')
  const [editTier, setEditTier] = useState<SupplierTier>('medium')
  const [editStatus, setEditStatus] = useState<SupplierStatus>('pending')

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
    if (!tier || !status) {
      setErr('Please select Tier and Status.')
      return
    }
    try {
      await createSupplier({ name, tier, status, description: null, website: null })
      setName('')
      setTier('')
      setStatus('')
      setShowForm(false)
      load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to create')
    }
  }

  const startEdit = (s: Supplier) => {
    setEditing(s)
    setEditName(s.name)
    setEditTier(s.tier)
    setEditStatus(s.status)
    setShowForm(false)
    setErr(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const cancelEdit = () => {
    setEditing(null)
  }

  const onSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editing) return
    setErr(null)
    try {
      await updateSupplier(editing.id, { name: editName, tier: editTier, status: editStatus })
      setEditing(null)
      load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to save')
    }
  }

  const onDelete = async (s: Supplier) => {
    const ok = window.confirm(
      `Delete supplier "${s.name}"? Assessments and documents for this supplier will be removed. This cannot be undone.`,
    )
    if (!ok) return
    setErr(null)
    try {
      await deleteSupplier(s.id)
      if (editing?.id === s.id) setEditing(null)
      load()
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Failed to delete')
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Suppliers</h1>
          <p className="muted">Sorted by risk score (highest first)</p>
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={() => {
            setShowForm((was) => {
              const opening = !was
              if (opening) setEditing(null)
              return opening
            })
          }}
        >
          {showForm ? 'Cancel' : 'Add supplier'}
        </button>
      </header>

      {showForm && (
        <form className="card form-create" onSubmit={onCreate}>
          <div className="form-field">
            <label htmlFor="new-name">Name</label>
            <input
              id="new-name"
              required
              placeholder="Supplier name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="new-tier">Tier</label>
            <select
              id="new-tier"
              required
              value={tier}
              onChange={(e) => setTier(e.target.value as SupplierTier | '')}
            >
              <option value="" disabled>
                Select tier...
              </option>
              <option value="critical">critical</option>
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="new-status">Status</label>
            <select
              id="new-status"
              required
              value={status}
              onChange={(e) => setStatus(e.target.value as SupplierStatus | '')}
            >
              <option value="" disabled>
                Select status...
              </option>
              <option value="pending">pending</option>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </div>
          <div className="form-field-submit">
            <button className="btn primary" type="submit">
              Create
            </button>
          </div>
        </form>
      )}

      {editing && (
        <form className="card form-create" onSubmit={onSaveEdit}>
          <p className="form-edit-banner muted small">
            Editing <strong>{editing.name}</strong>
          </p>
          <div className="form-field">
            <label htmlFor="edit-name">Name</label>
            <input
              id="edit-name"
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="edit-tier">Tier</label>
            <select id="edit-tier" value={editTier} onChange={(e) => setEditTier(e.target.value as SupplierTier)}>
              <option value="critical">critical</option>
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="edit-status">Status</label>
            <select id="edit-status" value={editStatus} onChange={(e) => setEditStatus(e.target.value as SupplierStatus)}>
              <option value="pending">pending</option>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </div>
          <div className="form-field">
            <span className="form-field-label-gap" aria-hidden="true">
              {'\u00a0'}
            </span>
            <div className="form-field-action">
              <button type="button" className="btn" onClick={cancelEdit}>
                Cancel
              </button>
              <button className="btn primary" type="submit">
                Save
              </button>
            </div>
          </div>
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
                <th className="actions-col">Actions</th>
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
                  <td className="actions-cell">
                    <Link className="link" to={`/suppliers/${s.id}`}>
                      Open
                    </Link>
                    <button type="button" className="btn btn-inline" onClick={() => startEdit(s)}>
                      Edit
                    </button>
                    <button type="button" className="btn btn-inline danger" onClick={() => onDelete(s)}>
                      Delete
                    </button>
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
