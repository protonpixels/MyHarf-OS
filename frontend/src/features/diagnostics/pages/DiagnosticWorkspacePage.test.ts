import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ApiClientError } from '../../../api/errors'
import type { Customer } from '../../customers/types'
import { getCustomer } from '../../customers/customerService'
import { archiveDiagnostic, getDiagnostic, updateDiagnostic } from '../diagnosticService'
import { listDiagnosticFindings } from '../findingService'
import DiagnosticWorkspacePage from './DiagnosticWorkspacePage.vue'
import type { Diagnostic } from '../types'

vi.mock('../../customers/customerService', () => ({ getCustomer: vi.fn() }))
vi.mock('../diagnosticService', () => ({
  archiveDiagnostic: vi.fn(),
  getDiagnostic: vi.fn(),
  updateDiagnostic: vi.fn(),
}))
vi.mock('../findingService', () => ({
  archiveFinding: vi.fn(),
  createFinding: vi.fn(),
  getFinding: vi.fn(),
  listDiagnosticFindings: vi.fn(),
  updateFinding: vi.fn(),
}))

const diagnostic: Diagnostic = {
  id: 31,
  customer_id: 12,
  website_url: 'https://example.com/',
  status: 'planned',
  summary: 'Review the inquiry path.',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}
const customer: Customer = {
  id: 12,
  name: 'Jordan Reyes',
  business_name: 'North Star Roofing',
  email: null,
  phone: null,
  status: 'active',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}
const linkStub = { props: ['to'], template: '<a :href="JSON.stringify(to)"><slot /></a>' }
const mountPage = (diagnosticId = '31') => mount(DiagnosticWorkspacePage, {
  props: { diagnosticId },
  global: { stubs: { RouterLink: linkStub } },
})

function mockDialogMethods() {
  vi.spyOn(HTMLDialogElement.prototype, 'showModal').mockImplementation(function (this: HTMLDialogElement) {
    this.setAttribute('open', '')
  })
  vi.spyOn(HTMLDialogElement.prototype, 'close').mockImplementation(function (this: HTMLDialogElement) {
    this.removeAttribute('open')
  })
}

describe('diagnostic workspace', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getDiagnostic).mockResolvedValue(diagnostic)
    vi.mocked(getCustomer).mockResolvedValue(customer)
    vi.mocked(listDiagnosticFindings).mockResolvedValue([])
  })
  afterEach(() => vi.restoreAllMocks())

  it('shows loading while the diagnostic is being retrieved', () => {
    vi.mocked(getDiagnostic).mockReturnValue(new Promise(() => {}))
    const wrapper = mountPage()
    expect(wrapper.get('[role="status"]').text()).toContain('Loading diagnostic')
  })

  it('shows a not-found state for a missing diagnostic', async () => {
    vi.mocked(getDiagnostic).mockRejectedValue(new ApiClientError('Diagnostic not found', 404))
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.text()).toContain('Diagnostic not found')
    expect(wrapper.find('select').exists()).toBe(false)
  })

  it('shows diagnostic fields and resolves the associated customer', async () => {
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.text()).toContain('https://example.com/')
    expect(wrapper.text()).toContain('Review the inquiry path.')
    expect(wrapper.text()).toContain('Planned')
    expect(wrapper.text()).toContain('Jordan Reyes')
    expect(wrapper.text()).toContain('Nov 10, 2026')
    expect(getCustomer).toHaveBeenCalledWith(12)
    expect(wrapper.find('a[href*="customer-overview"]').exists()).toBe(true)
  })

  it('keeps the diagnostic visible when customer lookup fails', async () => {
    vi.mocked(getCustomer).mockRejectedValue(new ApiClientError('Customer unavailable', 503))
    const wrapper = mountPage()
    await flushPromises()
    expect(wrapper.text()).toContain('https://example.com/')
    expect(wrapper.text()).toContain('Customer information is unavailable')
    expect(wrapper.text()).not.toContain('Diagnostic didn’t load')
  })

  it('reloads when diagnosticId changes and ignores an older response', async () => {
    let resolve31!: (record: Diagnostic) => void
    let resolve32!: (record: Diagnostic) => void
    vi.mocked(getDiagnostic).mockImplementation((id) => new Promise((resolve) => {
      if (id === 31) resolve31 = resolve
      else resolve32 = resolve
    }))
    const wrapper = mountPage('31')
    await wrapper.setProps({ diagnosticId: '32' })
    const diagnostic32 = { ...diagnostic, id: 32, website_url: 'https://thirty-two.example/' }
    resolve32(diagnostic32)
    await flushPromises()
    resolve31(diagnostic)
    await flushPromises()
    expect(wrapper.text()).toContain('https://thirty-two.example/')
    expect(wrapper.text()).not.toContain('https://example.com/')
  })

  it('edits website and clears summary with empty string, without sending customer_id', async () => {
    mockDialogMethods()
    vi.mocked(updateDiagnostic).mockResolvedValue({ ...diagnostic, summary: '' })
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('button').trigger('click')
    await wrapper.get('#edit-diagnostic-website-url').setValue('https://updated.example')
    await wrapper.get('#edit-diagnostic-summary').setValue('')
    await wrapper.get('dialog[aria-labelledby="diagnostic-edit-title"] form').trigger('submit')
    await flushPromises()
    expect(updateDiagnostic).toHaveBeenCalledWith(31, { website_url: 'https://updated.example', summary: '' })
    expect(JSON.stringify(vi.mocked(updateDiagnostic).mock.calls[0]?.[1])).not.toContain('customer_id')
    expect(wrapper.text()).toContain('Diagnostic details saved.')
  })

  it('preserves edited values and presents backend field validation errors', async () => {
    mockDialogMethods()
    vi.mocked(updateDiagnostic).mockRejectedValue(new ApiClientError('Invalid website', 422, [
      { location: ['body', 'website_url'], message: 'Website URL is invalid.' },
    ]))
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('button').trigger('click')
    await wrapper.get('#edit-diagnostic-website-url').setValue('https://entered.example')
    await wrapper.get('dialog[aria-labelledby="diagnostic-edit-title"] form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Website URL is invalid.')
    expect((wrapper.get('#edit-diagnostic-website-url').element as HTMLInputElement).value).toBe('https://entered.example')
  })

  it('updates diagnostic status through PATCH', async () => {
    vi.mocked(updateDiagnostic).mockResolvedValue({ ...diagnostic, status: 'completed' })
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-status').setValue('completed')
    await flushPromises()
    expect(updateDiagnostic).toHaveBeenCalledWith(31, { status: 'completed' })
    expect(wrapper.text()).toContain('Diagnostic status updated.')
  })

  it('ignores a stale status mutation after navigating to a different diagnostic', async () => {
    let resolveUpdate!: (value: Diagnostic) => void
    vi.mocked(getDiagnostic).mockImplementation(async (id) => id === 31
      ? diagnostic
      : { ...diagnostic, id: 32, website_url: 'https://thirty-two.example/' })
    vi.mocked(updateDiagnostic).mockReturnValue(new Promise((resolve) => { resolveUpdate = resolve }))
    const wrapper = mountPage('31')
    await flushPromises()
    await wrapper.get('#diagnostic-status').setValue('completed')
    await wrapper.setProps({ diagnosticId: '32' })
    await flushPromises()
    expect(wrapper.text()).toContain('https://thirty-two.example/')
    resolveUpdate({ ...diagnostic, status: 'completed' })
    await flushPromises()
    expect(wrapper.text()).toContain('https://thirty-two.example/')
    expect(wrapper.text()).not.toContain('Diagnostic status updated.')
  })

  it('shows status update failures and restores the saved status selection', async () => {
    vi.mocked(updateDiagnostic).mockRejectedValue(new ApiClientError('Status update conflict', 409))
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-status').setValue('completed')
    await flushPromises()
    expect(wrapper.get('#diagnostic-status').element).toHaveProperty('value', 'planned')
    expect(wrapper.get('[role="alert"]').text()).toContain('Status update conflict')
  })

  it('requires confirmation to archive and makes the resulting record read-only', async () => {
    mockDialogMethods()
    vi.mocked(archiveDiagnostic).mockResolvedValue({ ...diagnostic, status: 'archived' })
    const wrapper = mountPage()
    await flushPromises()
    const archiveButton = wrapper.findAll('button').find((button) => button.text() === 'Archive diagnostic')
    await archiveButton?.trigger('click')
    expect(wrapper.get('dialog[aria-labelledby="diagnostic-archive-title"]').attributes('open')).toBeDefined()
    await wrapper.get('dialog[aria-labelledby="diagnostic-archive-title"] button.button--secondary').trigger('click')
    expect(archiveDiagnostic).not.toHaveBeenCalled()

    const secondArchiveButton = wrapper.findAll('button').find((button) => button.text() === 'Archive diagnostic')
    await secondArchiveButton?.trigger('click')
    await wrapper.get('dialog[aria-labelledby="diagnostic-archive-title"] button.button--danger').trigger('click')
    await flushPromises()
    expect(archiveDiagnostic).toHaveBeenCalledWith(31)
    expect(wrapper.text()).toContain('read-only')
    expect(wrapper.find('#diagnostic-status').exists()).toBe(false)
    expect(wrapper.find('.workspace-actions button').exists()).toBe(false)
    expect(wrapper.find('.findings-heading button').exists()).toBe(false)
  })
})
