export type DiagnosticStatus = 'planned' | 'in_progress' | 'completed' | 'cancelled' | 'archived'

export interface Diagnostic {
  id: number
  customer_id: number
  website_url: string
  status: DiagnosticStatus
  summary: string | null
  created_at: string
  updated_at: string
}

export interface DiagnosticCreatePayload {
  website_url: string
  summary?: string
}
