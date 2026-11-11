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

export type EditableDiagnosticStatus = Exclude<DiagnosticStatus, 'archived'>

export interface DiagnosticUpdatePayload {
  website_url?: string
  summary?: string
  status?: EditableDiagnosticStatus
}

export type FindingStatus = 'identified' | 'reviewed' | 'dismissed' | 'archived'
export type EditableFindingStatus = Exclude<FindingStatus, 'archived'>

export interface Finding {
  id: number
  diagnostic_id: number
  title: string
  description: string | null
  page_url: string | null
  evidence: string | null
  status: FindingStatus
  created_at: string
  updated_at: string
}

export interface FindingCreatePayload {
  title: string
  description?: string
  page_url?: string
  evidence?: string
}

export interface FindingUpdatePayload {
  title: string
  description: string
  page_url?: string
  evidence: string
  status: EditableFindingStatus
}
