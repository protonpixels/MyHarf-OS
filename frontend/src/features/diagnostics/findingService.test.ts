import { beforeEach, describe, expect, it, vi } from 'vitest'
import http from '../../api/http'
import { archiveFinding, createFinding, getFinding, listDiagnosticFindings, updateFinding } from './findingService'
import type { Finding } from './types'

vi.mock('../../api/http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))

const finding: Finding = {
  id: 71,
  diagnostic_id: 31,
  title: 'Contact form is hard to find',
  description: null,
  page_url: null,
  evidence: null,
  status: 'identified',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}

describe('finding service', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists findings from the diagnostic-scoped endpoint', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: [finding] })
    await expect(listDiagnosticFindings(31)).resolves.toEqual([finding])
    expect(http.get).toHaveBeenCalledWith('/diagnostics/31/findings')
  })

  it('retrieves one finding by ID', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: finding })
    await expect(getFinding(71)).resolves.toEqual(finding)
    expect(http.get).toHaveBeenCalledWith('/findings/71')
  })

  it('creates a finding under the diagnostic path without duplicating diagnostic_id in its body', async () => {
    vi.mocked(http.post).mockResolvedValue({ data: finding })
    const payload = { title: finding.title, description: '' }
    await expect(createFinding(31, payload)).resolves.toEqual(finding)
    expect(http.post).toHaveBeenCalledWith('/diagnostics/31/findings', payload)
    expect(JSON.stringify(vi.mocked(http.post).mock.calls[0]?.[1])).not.toContain('diagnostic_id')
  })

  it('updates only finding fields and uses the finding ID path', async () => {
    vi.mocked(http.patch).mockResolvedValue({ data: finding })
    const payload = { title: finding.title, description: '', evidence: '', status: 'reviewed' as const }
    await expect(updateFinding(71, payload)).resolves.toEqual(finding)
    expect(http.patch).toHaveBeenCalledWith('/findings/71', payload)
    expect(JSON.stringify(vi.mocked(http.patch).mock.calls[0]?.[1])).not.toContain('diagnostic_id')
  })

  it('archives through DELETE and propagates normalized client errors', async () => {
    vi.mocked(http.delete).mockResolvedValue({ data: { ...finding, status: 'archived' } })
    await expect(archiveFinding(71)).resolves.toMatchObject({ status: 'archived' })
    expect(http.delete).toHaveBeenCalledWith('/findings/71')

    const failure = new Error('Not found')
    vi.mocked(http.get).mockRejectedValue(failure)
    await expect(getFinding(999)).rejects.toBe(failure)
  })
})
