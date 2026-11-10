import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ApiClientError } from '../../api/errors'
import CustomerCreatePage from './pages/CustomerCreatePage.vue'
import CustomerEditPage from './pages/CustomerEditPage.vue'
import CustomerDetailPage from './pages/CustomerDetailPage.vue'
import { archiveCustomer, createCustomer, getCustomer, updateCustomer } from './customerService'
import type { Customer } from './types'

vi.mock('./customerService', () => ({
  archiveCustomer: vi.fn(),
  createCustomer: vi.fn(),
  getCustomer: vi.fn(),
  listCustomers: vi.fn(),
  updateCustomer: vi.fn(),
}))

const record: Customer = {
  id: 17,
  name: 'Jordan Reyes',
  business_name: 'North Star Roofing',
  email: 'jordan@example.com',
  phone: '555-0167',
  status: 'active',
  created_at: '2026-02-01T10:00:00Z',
  updated_at: '2026-02-03T12:30:00Z',
}
const linkStub = { props: ['to'], template: '<a><slot /></a>' }
const mountOptions = { global: { stubs: { RouterLink: linkStub } } }

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('customer create and edit pages', () => {
  it('submits normalized create data and shows success feedback', async () => {
    vi.mocked(createCustomer).mockResolvedValue(record)
    const wrapper = mount(CustomerCreatePage, mountOptions)
    await wrapper.get('#customer-name').setValue('  Jordan Reyes  ')
    await wrapper.get('#customer-business-name').setValue(' ')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createCustomer).toHaveBeenCalledWith({ name: 'Jordan Reyes', business_name: null, email: null, phone: null })
    expect(wrapper.text()).toContain('Customer created')
    expect(wrapper.text()).toContain('Jordan Reyes has been added')
  })

  it('shows backend create validation errors and preserves entered input', async () => {
    vi.mocked(createCustomer).mockRejectedValue(new ApiClientError('Invalid email', 422, [
      { location: ['body', 'email'], message: 'Enter a valid email.' },
    ]))
    const wrapper = mount(CustomerCreatePage, mountOptions)
    await wrapper.get('#customer-name').setValue('Jordan Reyes')
    await wrapper.get('#customer-email').setValue('jordan@example.com')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Enter a valid email.')
    expect((wrapper.get('#customer-name').element as HTMLInputElement).value).toBe('Jordan Reyes')
  })

  it('loads and updates a customer, then reports success', async () => {
    vi.mocked(getCustomer).mockResolvedValue(record)
    vi.mocked(updateCustomer).mockResolvedValue({ ...record, name: 'Jordan M. Reyes' })
    const wrapper = mount(CustomerEditPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('#customer-name').setValue('Jordan M. Reyes')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(getCustomer).toHaveBeenCalledWith(17)
    expect(updateCustomer).toHaveBeenCalledWith(17, {
      name: 'Jordan M. Reyes', business_name: 'North Star Roofing', email: 'jordan@example.com', phone: '555-0167',
    })
    expect(wrapper.text()).toContain('Customer details saved.')
  })

  it('shows failed update feedback without clearing entered values', async () => {
    vi.mocked(getCustomer).mockResolvedValue(record)
    vi.mocked(updateCustomer).mockRejectedValue(new ApiClientError('Customer update failed', 409))
    const wrapper = mount(CustomerEditPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('#customer-name').setValue('Changed name')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Customer update failed')
    expect((wrapper.get('#customer-name').element as HTMLInputElement).value).toBe('Changed name')
  })

  it('handles a missing customer response', async () => {
    vi.mocked(getCustomer).mockRejectedValue(new ApiClientError('Customer not found', 404))
    const wrapper = mount(CustomerEditPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    expect(wrapper.text()).toContain('Customer not found')
  })
})

describe('customer archive confirmation', () => {
  function mockDialogMethods() {
    vi.spyOn(HTMLDialogElement.prototype, 'showModal').mockImplementation(function (this: HTMLDialogElement) {
      this.setAttribute('open', '')
    })
    vi.spyOn(HTMLDialogElement.prototype, 'close').mockImplementation(function (this: HTMLDialogElement) {
      this.removeAttribute('open')
    })
  }

  it('requires confirmation and supports cancelling without an API call', async () => {
    vi.mocked(getCustomer).mockResolvedValue(record)
    mockDialogMethods()
    const wrapper = mount(CustomerDetailPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('button.button--danger').trigger('click')
    expect(wrapper.get('dialog').attributes('open')).toBeDefined()
    expect(wrapper.text()).toContain('does not permanently delete data')

    await wrapper.get('dialog button.button--secondary').trigger('click')
    expect(wrapper.get('dialog').attributes('open')).toBeUndefined()
    expect(archiveCustomer).not.toHaveBeenCalled()
  })

  it('closes the confirmation with Escape via the dialog cancel event', async () => {
    vi.mocked(getCustomer).mockResolvedValue(record)
    mockDialogMethods()
    const wrapper = mount(CustomerDetailPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('button.button--danger').trigger('click')
    const event = new Event('cancel', { bubbles: true, cancelable: true })
    wrapper.get('dialog').element.dispatchEvent(event)
    await flushPromises()

    expect(wrapper.get('dialog').attributes('open')).toBeUndefined()
    expect(archiveCustomer).not.toHaveBeenCalled()
  })

  it('archives after confirmation and presents the customer as archived', async () => {
    vi.mocked(getCustomer).mockResolvedValue(record)
    vi.mocked(archiveCustomer).mockResolvedValue({ ...record, status: 'archived' })
    mockDialogMethods()
    const wrapper = mount(CustomerDetailPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('button.button--danger').trigger('click')
    await wrapper.get('dialog button.button--danger').trigger('click')
    await flushPromises()

    expect(archiveCustomer).toHaveBeenCalledWith(17)
    expect(wrapper.text()).toContain('This customer is archived')
    expect(wrapper.text()).toContain('Archived')
    expect(wrapper.find('dialog').exists()).toBe(false)
    expect(wrapper.findAll('button.button--danger')).toHaveLength(0)
  })

  it('keeps the confirmation open and shows archive API failure', async () => {
    vi.mocked(getCustomer).mockResolvedValue(record)
    vi.mocked(archiveCustomer).mockRejectedValue(new ApiClientError('Archive is unavailable', 409))
    mockDialogMethods()
    const wrapper = mount(CustomerDetailPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    await wrapper.get('button.button--danger').trigger('click')
    await wrapper.get('dialog button.button--danger').trigger('click')
    await flushPromises()

    expect(wrapper.get('dialog').attributes('open')).toBeDefined()
    expect(wrapper.get('[role="alert"]').text()).toContain('Archive is unavailable')
    expect(wrapper.text()).not.toContain('This customer is archived')
  })

  it('does not show an archive control for an archived customer', async () => {
    vi.mocked(getCustomer).mockResolvedValue({ ...record, status: 'archived' })
    const wrapper = mount(CustomerDetailPage, { props: { customerId: '17' }, ...mountOptions })
    await flushPromises()
    expect(wrapper.text()).toContain('This customer is archived')
    expect(wrapper.find('button.button--danger').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Restore customer')
  })
})
