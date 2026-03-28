export type SupplierTier = 'critical' | 'high' | 'medium' | 'low'
export type SupplierStatus = 'active' | 'pending' | 'archived'
export type AnswerChoice = 'yes' | 'partial' | 'no'

export interface Supplier {
  id: string
  name: string
  description: string | null
  website: string | null
  tier: SupplierTier
  risk_score: number
  status: SupplierStatus
  created_at: string
  updated_at: string
}

export interface Question {
  id: string
  text: string
  category: string
  sort_order: number
  max_points: number
}

export interface AssessmentResponse {
  id: string
  question_id: string
  answer: AnswerChoice
  question: Question
  updated_at: string
}

export interface SupplierDocument {
  id: string
  supplier_id: string
  original_filename: string
  content_type: string | null
  created_at: string
}
