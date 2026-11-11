import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ApiClientError } from '../../../api/errors'
import CustomerDiagnosticsSection from './CustomerDiagnosticsSection.vue'
import { listCustomerDiagnostics } from '../diagnosticService'
import type { Diagnostic } from '../types'

vi.mock('../diagnosticService', () => ({
  listCustomerDiagnostics: vi.fn(),
}))

const planned: Diagnostic = {
  id: 31,
  customer_id: 12,
  website_url: 'https://example.com/',
  status: 'planned',
  summary: 'Check the main service pages.',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}
const archived: Diagnostic = { ...planned, id: 32, website_url: 'https://old.example.com/', status: 'archived' }
const linkStub = { props: ['to', 'ariaDisabled'], template: '<a :href="JSON.stringify(to)" :aria-disabled="ariaDisabled"><slot /></a>' }
const mountOptions = { global: { stubs: { RouterLink: linkStub } } }

describe('customer diagnostics section', () => {
  beforeEach(() => vi.clearAllMocks())
  afterEach(() => vi.restoreAllMocks())

  it('shows a loading state while diagnostics are being fetched', () => {
    vi.mocked(listCustomerDiagnostics).mockReturnValue(new Promise(() => {}))
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    expect(wrapper.get('[role="status"]').text()).toContain('Loading diagnostics')
  })

  it('shows an empty state when there are no diagnostics', async () => {
    vi.mocked(listCustomerDiagnostics).mockResolvedValue([])
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    await flushPromises()

    expect(wrapper.text()).toContain('No diagnostics yet')
    expect(wrapper.text()).toContain('Create first diagnostic')
  })

  it('shows populated diagnostics and hides archived ones by default', async () => {
    vi.mocked(listCustomerDiagnostics).mockResolvedValue([planned, archived])
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    await flushPromises()

    expect(wrapper.text()).toContain('https://example.com/')
    expect(wrapper.text()).toContain('Check the main service pages.')
    expect(wrapper.text()).toContain('Created Nov 10, 2026')
    expect(wrapper.text()).not.toContain('https://old.example.com/')
    expect(wrapper.find('a[href*="diagnostic-workspace"]').exists()).toBe(true)
  })

  it('includes archived diagnostics when requested', async () => {
    vi.mocked(listCustomerDiagnostics).mockResolvedValue([planned, archived])
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('input[type="checkbox"]').setValue(true)

    expect(wrapper.text()).toContain('https://old.example.com/')
    expect(wrapper.text()).toContain('Archived')
  })

  it('provides create and detail navigation links', async () => {
    vi.mocked(listCustomerDiagnostics).mockResolvedValue([planned])
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    await flushPromises()

    expect(wrapper.find('a[aria-disabled="false"]').attributes('href')).toContain('diagnostic-create')
    expect(wrapper.find('a[href*="diagnostic-workspace"]').attributes('href')).toContain('diagnosticId')
  })

  it('shows an API error with a retry action', async () => {
    vi.mocked(listCustomerDiagnostics).mockRejectedValue(new ApiClientError('Customer not found', 404))
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    await flushPromises()

    expect(wrapper.text()).toContain('Diagnostics didn’t load')
    expect(wrapper.text()).toContain('This customer could not be found.')
    expect(wrapper.text()).toContain('Try again')
  })

  it('does not offer creation for archived customers', async () => {
    vi.mocked(listCustomerDiagnostics).mockResolvedValue([])
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'archived' }, ...mountOptions })
    await flushPromises()

    expect(wrapper.text()).toContain('backend does not allow new diagnostics')
    expect(wrapper.text()).not.toContain('New diagnostic')
    expect(wrapper.text()).not.toContain('Create first diagnostic')
  })

  it('reloads for a different customer and ignores a slower previous response', async () => {
    let resolve12!: (rows: Diagnostic[]) => void
    let resolve13!: (rows: Diagnostic[]) => void
    vi.mocked(listCustomerDiagnostics).mockImplementation((customerId) => new Promise((resolve) => {
      if (customerId === 12) resolve12 = resolve
      else resolve13 = resolve
    }))
    const wrapper = mount(CustomerDiagnosticsSection, { props: { customerId: 12, customerStatus: 'active' }, ...mountOptions })
    await wrapper.setProps({ customerId: 13 })
    const for13 = { ...planned, customer_id: 13, id: 41, website_url: 'https://thirteen.example/' }
    resolve13([for13])
    await flushPromises()
    resolve12([planned])
    await flushPromises()

    expect(listCustomerDiagnostics).toHaveBeenNthCalledWith(1, 12)
    expect(listCustomerDiagnostics).toHaveBeenNthCalledWith(2, 13)
    expect(wrapper.text()).toContain('https://thirteen.example/')
    expect(wrapper.text()).not.toContain('https://example.com/')
  })
})
