import type { ApiClientError, ApiIssue } from '../../api/errors'
import type { DiagnosticCreatePayload, DiagnosticUpdatePayload } from './types'

export interface DiagnosticFormValues {
  website_url: string
  summary: string
}

export type DiagnosticField = keyof DiagnosticCreatePayload
export type DiagnosticFieldErrors = Partial<Record<DiagnosticField, string>>

export function validateDiagnosticForm(values: DiagnosticFormValues): DiagnosticFieldErrors {
  const errors: DiagnosticFieldErrors = {}
  const websiteUrl = values.website_url.trim()

  if (!websiteUrl) errors.website_url = 'Enter the website URL.'
  else {
    try {
      const parsed = new URL(websiteUrl)
      if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname) {
        errors.website_url = 'Enter a valid website URL beginning with http:// or https://.'
      }
    } catch {
      errors.website_url = 'Enter a valid website URL beginning with http:// or https://.'
    }
  }

  return errors
}

export function normalizeDiagnosticForm(values: DiagnosticFormValues): DiagnosticCreatePayload {
  const payload: DiagnosticCreatePayload = { website_url: values.website_url.trim() }
  const summary = values.summary.trim()
  if (summary) payload.summary = summary
  return payload
}

export function normalizeDiagnosticUpdateForm(values: DiagnosticFormValues): DiagnosticUpdatePayload {
  return { website_url: values.website_url.trim(), summary: values.summary.trim() }
}

export function mapDiagnosticApiIssues(issues: ApiIssue[]): {
  fieldErrors: DiagnosticFieldErrors
  generalErrors: string[]
} {
  const fieldErrors: DiagnosticFieldErrors = {}
  const generalErrors: string[] = []

  for (const issue of issues) {
    const field = issue.location?.find((part): part is DiagnosticField =>
      part === 'website_url' || part === 'summary',
    )
    if (field && !fieldErrors[field]) fieldErrors[field] = issue.message
    else if (!field) generalErrors.push(issue.message)
  }

  return { fieldErrors, generalErrors }
}

export function diagnosticErrorMessages(error: unknown): {
  fieldErrors: DiagnosticFieldErrors
  generalErrors: string[]
} {
  if (error instanceof Error && 'issues' in error) {
    const apiError = error as ApiClientError
    if (apiError.issues.length) return mapDiagnosticApiIssues(apiError.issues)
    return { fieldErrors: {}, generalErrors: [apiError.message] }
  }
  return {
    fieldErrors: {},
    generalErrors: [error instanceof Error ? error.message : 'The diagnostic could not be saved. Please try again.'],
  }
}
