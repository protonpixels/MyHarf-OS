import { beforeEach, describe, expect, it, vi } from 'vitest'
import http from '../../api/http'
import { archiveDiagnostic, createCustomerDiagnostic, getDiagnostic, listCustomerDiagnostics, updateDiagnostic } from './diagnosticService'
import type { Diagnostic } from './types'

vi.mock('../../api/http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
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

  it('retrieves a diagnostic by its ID', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: diagnostic })
    await expect(getDiagnostic(31)).resolves.toEqual(diagnostic)
    expect(http.get).toHaveBeenCalledWith('/diagnostics/31')
  })

  it('patches only supplied diagnostic fields and never a parent ID', async () => {
    vi.mocked(http.patch).mockResolvedValue({ data: diagnostic })
    const payload = { website_url: 'https://changed.example', summary: '' }
    await expect(updateDiagnostic(31, payload)).resolves.toEqual(diagnostic)
    expect(http.patch).toHaveBeenCalledWith('/diagnostics/31', payload)
    expect(JSON.stringify(vi.mocked(http.patch).mock.calls[0]?.[1])).not.toContain('customer_id')
  })

  it('archives a diagnostic through DELETE', async () => {
    vi.mocked(http.delete).mockResolvedValue({ data: { ...diagnostic, status: 'archived' } })
    await expect(archiveDiagnostic(31)).resolves.toMatchObject({ status: 'archived' })
    expect(http.delete).toHaveBeenCalledWith('/diagnostics/31')
  })
})
