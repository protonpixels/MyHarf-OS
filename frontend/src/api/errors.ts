export interface ApiIssue {
  location?: Array<string | number>
  message: string
  code?: string
}

export class ApiClientError extends Error {
  readonly status?: number
  readonly issues: ApiIssue[]

  constructor(message: string, status?: number, issues: ApiIssue[] = []) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.issues = issues
  }
}

type FastApiDetail = string | Array<{ loc?: Array<string | number>; msg?: string; type?: string }>

export function normalizeApiError(error: unknown): ApiClientError {
  const candidate = error as {
    message?: string
    response?: { status?: number; data?: { detail?: FastApiDetail; message?: string } }
  }
  const status = candidate?.response?.status
  const detail = candidate?.response?.data?.detail
  if (typeof detail === 'string') return new ApiClientError(detail, status)
  if (Array.isArray(detail)) {
    const issues = detail.map((issue) => ({
      location: issue.loc,
      message: issue.msg ?? 'The submitted value is invalid.',
      code: issue.type,
    }))
    return new ApiClientError(issues[0]?.message ?? 'The request could not be processed.', status, issues)
  }
  const message = candidate?.response?.data?.message ?? candidate?.message ?? 'A network error occurred.'
  return new ApiClientError(message, status)
}
