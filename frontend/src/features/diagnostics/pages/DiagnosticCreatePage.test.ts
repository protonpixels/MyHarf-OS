import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ApiClientError } from '../../../api/errors'
import type { Customer } from '../../customers/types'
import { getCustomer } from '../../customers/customerService'
import { createCustomerDiagnostic } from '../diagnosticService'
import DiagnosticCreatePage from './DiagnosticCreatePage.vue'
import type { Diagnostic } from '../types'

const { push } = vi.hoisted(() => ({ push: vi.fn() }))
vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return { ...actual, useRouter: () => ({ push }) }
})
vi.mock('../../customers/customerService', () => ({ getCustomer: vi.fn() }))
vi.mock('../diagnosticService', () => ({ createCustomerDiagnostic: vi.fn() }))

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
const diagnostic: Diagnostic = {
  id: 31,
  customer_id: 12,
  website_url: 'https://example.com/',
  status: 'planned',
  summary: 'Initial assessment',
  created_at: '2026-11-10T12:00:00Z',
  updated_at: '2026-11-10T12:00:00Z',
}
const linkStub = { props: ['to'], template: '<a :href="JSON.stringify(to)"><slot /></a>' }
const mountPage = (customerId = '12') => mount(DiagnosticCreatePage, {
  props: { customerId },
  global: { stubs: { RouterLink: linkStub } },
})

describe('diagnostic creation page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getCustomer).mockResolvedValue(customer)
  })
  afterEach(() => vi.restoreAllMocks())

  it('validates that a website URL is required', async () => {
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('form').trigger('submit')

    expect(wrapper.text()).toContain('Enter the website URL.')
    expect(createCustomerDiagnostic).not.toHaveBeenCalled()
  })

  it('requires a valid HTTP or HTTPS URL', async () => {
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-website-url').setValue('example.com')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.text()).toContain('valid website URL')
    expect(createCustomerDiagnostic).not.toHaveBeenCalled()
  })

  it('creates with an optional summary and navigates to the diagnostic', async () => {
    vi.mocked(createCustomerDiagnostic).mockResolvedValue(diagnostic)
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-website-url').setValue(' https://example.com ')
    await wrapper.get('#diagnostic-summary').setValue(' Initial assessment ')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(getCustomer).toHaveBeenCalledWith(12)
    expect(createCustomerDiagnostic).toHaveBeenCalledWith(12, {
      website_url: 'https://example.com', summary: 'Initial assessment',
    })
    expect(push).toHaveBeenCalledWith({ name: 'diagnostic-workspace', params: { diagnosticId: 31 } })
  })

  it('omits a blank optional summary from the request body', async () => {
    vi.mocked(createCustomerDiagnostic).mockResolvedValue({ ...diagnostic, summary: null })
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-website-url').setValue('https://example.com')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createCustomerDiagnostic).toHaveBeenCalledWith(12, { website_url: 'https://example.com' })
  })

  it('shows backend validation errors and retains entered values', async () => {
    vi.mocked(createCustomerDiagnostic).mockRejectedValue(new ApiClientError('Invalid URL', 422, [
      { location: ['body', 'website_url'], message: 'URL is not acceptable.' },
    ]))
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-website-url').setValue('https://entered.example')
    await wrapper.get('#diagnostic-summary').setValue('Keep these notes')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('URL is not acceptable.')
    expect((wrapper.get('#diagnostic-website-url').element as HTMLInputElement).value).toBe('https://entered.example')
    expect((wrapper.get('#diagnostic-summary').element as HTMLTextAreaElement).value).toBe('Keep these notes')
  })

  it('shows a missing customer state', async () => {
    vi.mocked(getCustomer).mockRejectedValue(new ApiClientError('Customer not found', 404))
    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain('Customer not found')
    expect(wrapper.text()).toContain('Back to customers')
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('explains that an archived customer cannot receive a diagnostic', async () => {
    vi.mocked(getCustomer).mockResolvedValue({ ...customer, status: 'archived' })
    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain('Customer is archived')
    expect(wrapper.text()).toContain('does not allow new diagnostics')
    expect(wrapper.find('form').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Create diagnostic')
  })

  it('reloads customer context when the route customer changes and ignores stale responses', async () => {
    let resolve12!: (value: Customer) => void
    let resolve13!: (value: Customer) => void
    vi.mocked(getCustomer).mockImplementation((id) => new Promise((resolve) => {
      if (id === 12) resolve12 = resolve
      else resolve13 = resolve
    }))
    const wrapper = mountPage('12')
    await wrapper.setProps({ customerId: '13' })
    resolve13({ ...customer, id: 13, name: 'Customer Thirteen' })
    await flushPromises()
    expect(wrapper.text()).toContain('Customer Thirteen')
    resolve12(customer)
    await flushPromises()

    expect(wrapper.text()).toContain('Customer Thirteen')
    expect(wrapper.text()).not.toContain('Jordan Reyes')
  })

  it('shows the backend archived-customer conflict if status changes after page load', async () => {
    vi.mocked(createCustomerDiagnostic).mockRejectedValue(new ApiClientError('Cannot create a diagnostic for an archived customer', 409))
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-website-url').setValue('https://example.com')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Cannot create a diagnostic for an archived customer')
    expect((wrapper.get('#diagnostic-website-url').element as HTMLInputElement).value).toBe('https://example.com')
  })

  it('prevents duplicate submissions while a create request is pending', async () => {
    let finish!: (value: Diagnostic) => void
    vi.mocked(createCustomerDiagnostic).mockReturnValue(new Promise((resolve) => { finish = resolve }))
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.get('#diagnostic-website-url').setValue('https://example.com')
    await wrapper.get('form').trigger('submit')
    await wrapper.get('form').trigger('submit')

    expect(createCustomerDiagnostic).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Creating…')
    finish(diagnostic)
    await flushPromises()
    expect(push).toHaveBeenCalledTimes(1)
  })
})
