import { beforeEach, describe, expect, it, vi } from 'vitest'
import http from '../../api/http'
import { createCustomerDiagnostic, listCustomerDiagnostics } from './diagnosticService'
import type { Diagnostic } from './types'

vi.mock('../../api/http', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

const diagnostic: Diagnostic = {
  id: 31,
  customer_id: 12,
  website_url: 'https://example.com/',
  status: 'planned',
  summary: null,
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}

describe('diagnostic service', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists diagnostics through the customer-scoped endpoint', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: [diagnostic] })

    await expect(listCustomerDiagnostics(12)).resolves.toEqual([diagnostic])
    expect(http.get).toHaveBeenCalledWith('/customers/12/diagnostics')
  })

  it('creates a diagnostic with the customer ID in the path and only body fields in the payload', async () => {
    vi.mocked(http.post).mockResolvedValue({ data: diagnostic })
    const payload = { website_url: 'https://example.com', summary: 'Initial review' }

    await expect(createCustomerDiagnostic(12, payload)).resolves.toEqual(diagnostic)
    expect(http.post).toHaveBeenCalledWith('/customers/12/diagnostics', payload)
    expect(JSON.stringify(vi.mocked(http.post).mock.calls[0]?.[1])).not.toContain('customer_id')
  })

  it('propagates errors from the shared normalized API client', async () => {
    const failure = new Error('Customer not found')
    vi.mocked(http.get).mockRejectedValue(failure)

    await expect(listCustomerDiagnostics(404)).rejects.toBe(failure)
  })
})
