import type {
  AnswerChoice,
  AssessmentResponse,
  Question,
  Supplier,
  SupplierDocument,
  SupplierStatus,
  SupplierTier,
} from './types'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const t = await res.text()
    throw new Error(t || res.statusText)
  }
  return res.json() as Promise<T>
}

export async function fetchSuppliers(): Promise<Supplier[]> {
  const res = await fetch('/api/suppliers')
  return json<Supplier[]>(res)
}

export async function fetchRiskSummary(): Promise<Supplier[]> {
  const res = await fetch('/api/risk-summary')
  return json<Supplier[]>(res)
}

export async function createSupplier(body: {
  name: string
  description?: string | null
  website?: string | null
  tier: SupplierTier
  status: SupplierStatus
}): Promise<Supplier> {
  const res = await fetch('/api/suppliers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return json<Supplier>(res)
}

export async function getSupplier(id: string): Promise<Supplier> {
  const res = await fetch(`/api/suppliers/${id}`)
  return json<Supplier>(res)
}

export async function updateSupplier(
  id: string,
  body: Partial<{
    name: string
    description: string | null
    website: string | null
    tier: SupplierTier
    status: SupplierStatus
  }>,
): Promise<Supplier> {
  const res = await fetch(`/api/suppliers/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return json<Supplier>(res)
}

export async function fetchQuestions(supplierId: string): Promise<Question[]> {
  const res = await fetch(`/api/suppliers/${supplierId}/questions`)
  return json<Question[]>(res)
}

export async function fetchAssessment(supplierId: string): Promise<AssessmentResponse[]> {
  const res = await fetch(`/api/suppliers/${supplierId}/assessment`)
  return json<AssessmentResponse[]>(res)
}

export async function submitAssessment(
  supplierId: string,
  responses: { question_id: string; answer: AnswerChoice }[],
): Promise<AssessmentResponse[]> {
  const res = await fetch(`/api/suppliers/${supplierId}/assessment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ responses }),
  })
  return json<AssessmentResponse[]>(res)
}

export async function fetchDocuments(supplierId: string): Promise<SupplierDocument[]> {
  const res = await fetch(`/api/suppliers/${supplierId}/documents`)
  return json<SupplierDocument[]>(res)
}

export async function uploadDocument(supplierId: string, file: File): Promise<SupplierDocument> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`/api/suppliers/${supplierId}/documents`, {
    method: 'POST',
    body: fd,
  })
  return json<SupplierDocument>(res)
}

export async function sendChat(message: string, supplierId?: string): Promise<{ reply: string }> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, supplier_id: supplierId ?? null }),
  })
  return json<{ reply: string }>(res)
}
