import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  deleteSupplier,
  fetchAssessment,
  fetchDocuments,
  fetchQuestions,
  getSupplier,
  sendChat,
  submitAssessment,
  updateSupplier,
  uploadDocument,
} from '../api'
import type { AnswerChoice, AssessmentResponse, Question, Supplier, SupplierDocument } from '../types'

export default function SupplierDetail() {
  const { id } = useParams<{ id: string }>()
  const supplierId = id!

  const [supplier, setSupplier] = useState<Supplier | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [responses, setResponses] = useState<AssessmentResponse[]>([])
  const [docs, setDocs] = useState<SupplierDocument[]>([])
  const [answers, setAnswers] = useState<Record<string, AnswerChoice>>({})
  const [chat, setChat] = useState<{ role: 'user' | 'assistant'; text: string }[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState('')
  const [editTier, setEditTier] = useState<'critical' | 'high' | 'medium' | 'low'>('medium')
  const [editStatus, setEditStatus] = useState<'active' | 'pending' | 'archived'>('pending')
  const navigate = useNavigate()

  const load = async () => {
    if (!supplierId) return
    setErr(null)
    const [s, q, a, d] = await Promise.all([
      getSupplier(supplierId),
      fetchQuestions(supplierId),
      fetchAssessment(supplierId),
      fetchDocuments(supplierId),
    ])
    setSupplier(s)
    setQuestions(q.sort((x, y) => x.sort_order - y.sort_order))
    setResponses(a)
    setDocs(d)
    const map: Record<string, AnswerChoice> = {}
    for (const r of a) map[r.question_id] = r.answer
    setAnswers(map)
  }

  useEffect(() => {
    load().catch((e: Error) => setErr(e.message))
  }, [supplierId])

  const missingCount = useMemo(() => {
    const ids = new Set(questions.map((q) => q.id))
    return [...ids].filter((qid) => !answers[qid]).length
  }, [questions, answers])

  const saveAssessment = async (e: FormEvent) => {
    e.preventDefault()
    if (!supplierId) return
    const payload = questions.map((q) => ({
      question_id: q.id,
      answer: answers[q.id] ?? 'no',
    }))
    setBusy(true)
    setErr(null)
    try {
      const res = await submitAssessment(supplierId, payload)
      setResponses(res)
      const s = await getSupplier(supplierId)
      setSupplier(s)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setBusy(false)
    }
  }

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f || !supplierId) return
    setBusy(true)
    setErr(null)
    try {
      await uploadDocument(supplierId, f)
      setDocs(await fetchDocuments(supplierId))
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  const beginEdit = () => {
    if (!supplier) return
    setEditName(supplier.name)
    setEditTier(supplier.tier)
    setEditStatus(supplier.status)
    setIsEditing(true)
    setErr(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const saveSupplier = async (e: FormEvent) => {
    e.preventDefault()
    if (!supplier || !supplierId) return
    setBusy(true)
    setErr(null)
    try {
      const updated = await updateSupplier(supplierId, {
        name: editName,
        tier: editTier,
        status: editStatus,
      })
      setSupplier(updated)
      setIsEditing(false)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Update failed')
    } finally {
      setBusy(false)
    }
  }

  const removeSupplier = async () => {
    if (!supplier || !supplierId) return
    const ok = window.confirm('Delete supplier "' + supplier.name + '"? This cannot be undone.')
    if (!ok) return
    setBusy(true)
    setErr(null)
    try {
      await deleteSupplier(supplierId)
      navigate('/')
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Delete failed')
    } finally {
      setBusy(false)
    }
  }

  const ask = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !supplierId) return
    const userMsg = input.trim()
    setInput('')
    setChat((c) => [...c, { role: 'user', text: userMsg }])
    setBusy(true)
    setErr(null)
    try {
      const { reply } = await sendChat(userMsg, supplierId)
      setChat((c) => [...c, { role: 'assistant', text: reply }])
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Chat failed')
    } finally {
      setBusy(false)
    }
  }

  if (!supplier) {
    return (
      <div className="page">
        <p className="muted">{err ? err : 'Loading…'}</p>
        <Link className="link" to="/">
          Back
        </Link>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="breadcrumb">
        <Link className="link" to="/">
          Suppliers
        </Link>
        <span className="muted"> / </span>
        <span>{supplier.name}</span>
      </div>

      <header className="page-header">
        <div>
          <h1>{supplier.name}</h1>
          <p className="muted">
            Risk score: <strong>{supplier.risk_score.toFixed(1)}</strong> · tier{' '}
            <span className={`badge ${supplier.tier}`}>{supplier.tier}</span> · {supplier.status}
          </p>
          {supplier.website && (
            <p>
              <a href={supplier.website} target="_blank" rel="noreferrer">
                {supplier.website}
              </a>
            </p>
          )}
          {supplier.description && <p>{supplier.description}</p>}
        </div>
        <div>
          <button className="btn" type="button" onClick={beginEdit} disabled={busy}>
            Edit supplier
          </button>
          <button className="btn danger" type="button" onClick={removeSupplier} disabled={busy}>
            Delete supplier
          </button>
        </div>
      </header>

      {isEditing && (
        <form className="card form-create" onSubmit={saveSupplier}>
          <p className="form-edit-banner muted small">
            Editing supplier <strong>{supplier?.name}</strong>
          </p>
          <div className="form-field">
            <label htmlFor="detail-edit-name">Name</label>
            <input
              id="detail-edit-name"
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label htmlFor="detail-edit-tier">Tier</label>
            <select
              id="detail-edit-tier"
              value={editTier}
              onChange={(e) => setEditTier(e.target.value as 'critical' | 'high' | 'medium' | 'low')}
            >
              <option value="critical">critical</option>
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="detail-edit-status">Status</label>
            <select
              id="detail-edit-status"
              value={editStatus}
              onChange={(e) => setEditStatus(e.target.value as 'active' | 'pending' | 'archived')}
            >
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
              <button type="button" className="btn" onClick={() => setIsEditing(false)}>
                Cancel
              </button>
              <button className="btn primary" type="submit" disabled={busy}>
                Save
              </button>
            </div>
          </div>
        </form>
      )}

      {err && <div className="alert error">{err}</div>}

      <div className="grid-2">
        <section className="card">
          <h2>Assessment</h2>
          <p className="muted small">
            Higher risk score means more gaps. Answer all questions, then save. {missingCount > 0 && (
              <span className="warn"> {missingCount} unanswered (defaulting to “no”).</span>
            )}
          </p>
          <form onSubmit={saveAssessment}>
            <div className="stack">
              {questions.map((q) => (
                <div key={q.id} className="q-row">
                  <div>
                    <div className="q-text">{q.text}</div>
                    <div className="muted small">
                      {q.category} · weight {q.max_points}
                    </div>
                  </div>
                  <select
                    value={answers[q.id] ?? ''}
                    onChange={(e) =>
                      setAnswers((a) => ({
                        ...a,
                        [q.id]: e.target.value as AnswerChoice,
                      }))
                    }
                  >
                    <option value="" disabled>
                      Select…
                    </option>
                    <option value="yes">yes</option>
                    <option value="partial">partial</option>
                    <option value="no">no</option>
                  </select>
                </div>
              ))}
            </div>
            <button className="btn primary" type="submit" disabled={busy || questions.length === 0}>
              Save assessment
            </button>
          </form>

          {responses.length > 0 && (
            <div className="mt">
              <h3>Current responses</h3>
              <ul className="list">
                {responses.map((r) => (
                  <li key={r.id}>
                    <span className="muted">{r.question.category}:</span> {r.answer}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section className="card">
          <h2>Documents</h2>
          <p className="muted small">Upload PDF or text files for RAG (chunked & embedded).</p>
          <input type="file" accept=".pdf,.txt,.md" onChange={onUpload} disabled={busy} />
          <ul className="list mt">
            {docs.map((d) => (
              <li key={d.id}>
                {d.original_filename}{' '}
                <span className="muted small">({new Date(d.created_at).toLocaleString()})</span>
              </li>
            ))}
          </ul>
          {docs.length === 0 && <p className="muted">No documents yet.</p>}
        </section>
      </div>

      <section className="card chat">
        <h2>AI assistant</h2>
        <p className="muted small">
          Scoped to this supplier. Ask about assessment gaps or uploaded documents (citations from tools).
        </p>
        <div className="chat-log">
          {chat.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="role">{m.role}</div>
              {m.role === 'assistant' ? (
                <div className="msg-body markdown-body">
                  <ReactMarkdown>{m.text}</ReactMarkdown>
                </div>
              ) : (
                <div className="msg-body user-msg">{m.text}</div>
              )}
            </div>
          ))}
        </div>
        <form className="chat-form" onSubmit={ask}>
          <textarea
            rows={3}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. What gaps exist in incident handling? What do uploaded files say about access control?"
          />
          <button className="btn primary" type="submit" disabled={busy}>
            Send
          </button>
        </form>
      </section>
    </div>
  )
}
