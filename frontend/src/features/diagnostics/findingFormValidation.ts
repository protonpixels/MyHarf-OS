import type { ApiClientError, ApiIssue } from '../../api/errors'
import type { EditableFindingStatus, Finding, FindingCreatePayload, FindingUpdatePayload } from './types'

export interface FindingFormValues {
  title: string
  description: string
  page_url: string
  evidence: string
  status: EditableFindingStatus
}

export type FindingField = 'title' | 'description' | 'page_url' | 'evidence' | 'status'
export type FindingFieldErrors = Partial<Record<FindingField, string>>

export function findingToFormValues(finding?: Finding): FindingFormValues {
  return {
    title: finding?.title ?? '',
    description: finding?.description ?? '',
    page_url: finding?.page_url ?? '',
    evidence: finding?.evidence ?? '',
    status: finding?.status === 'reviewed' || finding?.status === 'dismissed' ? finding.status : 'identified',
  }
}

export function validateFindingForm(values: FindingFormValues, finding?: Finding): FindingFieldErrors {
  const errors: FindingFieldErrors = {}
  const title = values.title.trim()
  const pageUrl = values.page_url.trim()

  if (!title) errors.title = 'Enter a finding title.'
  else if (title.length > 250) errors.title = 'Title must be 250 characters or fewer.'

  if (pageUrl) {
    try {
      const parsed = new URL(pageUrl)
      if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname) {
        errors.page_url = 'Enter a valid page URL beginning with http:// or https://.'
      }
    } catch {
      errors.page_url = 'Enter a valid page URL beginning with http:// or https://.'
    }
  } else if (finding?.page_url) {
    errors.page_url = 'A page URL cannot be cleared. Keep the current URL or replace it with another valid URL.'
  }

  return errors
}

export function normalizeFindingCreateForm(values: FindingFormValues): FindingCreatePayload {
  const payload: FindingCreatePayload = { title: values.title.trim() }
  if (values.description.trim()) payload.description = values.description.trim()
  if (values.page_url.trim()) payload.page_url = values.page_url.trim()
  if (values.evidence.trim()) payload.evidence = values.evidence.trim()
  return payload
}

export function normalizeFindingUpdateForm(values: FindingFormValues): FindingUpdatePayload {
  const payload: FindingUpdatePayload = {
    title: values.title.trim(),
    description: values.description.trim(),
    evidence: values.evidence.trim(),
    status: values.status,
  }
  if (values.page_url.trim()) payload.page_url = values.page_url.trim()
  return payload
}

export function mapFindingApiIssues(issues: ApiIssue[]): { fieldErrors: FindingFieldErrors; generalErrors: string[] } {
  const fieldErrors: FindingFieldErrors = {}
  const generalErrors: string[] = []
  const fields: FindingField[] = ['title', 'description', 'page_url', 'evidence', 'status']

  for (const issue of issues) {
    const field = issue.location?.find((part): part is FindingField =>
      typeof part === 'string' && fields.includes(part as FindingField),
    )
    if (field && !fieldErrors[field]) fieldErrors[field] = issue.message
    else if (!field) generalErrors.push(issue.message)
  }
  return { fieldErrors, generalErrors }
}

export function findingErrorMessages(error: unknown): { fieldErrors: FindingFieldErrors; generalErrors: string[] } {
  if (error instanceof Error && 'issues' in error) {
    const apiError = error as ApiClientError
    if (apiError.issues.length) return mapFindingApiIssues(apiError.issues)
    return { fieldErrors: {}, generalErrors: [apiError.message] }
  }
  return {
    fieldErrors: {},
    generalErrors: [error instanceof Error ? error.message : 'The finding could not be saved. Please try again.'],
  }
}
