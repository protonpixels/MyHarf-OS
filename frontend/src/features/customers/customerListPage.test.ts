import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CustomerListPage from './pages/CustomerListPage.vue'
import { listCustomers } from './customerService'
import type { Customer } from './types'

vi.mock('./customerService', () => ({
  archiveCustomer: vi.fn(),
  createCustomer: vi.fn(),
  getCustomer: vi.fn(),
  listCustomers: vi.fn(),
  updateCustomer: vi.fn(),
}))

const customers: Customer[] = [
  { id: 1, name: 'Casey Morgan', business_name: 'Copper Peak Roofing', email: 'casey@copper.example', phone: '555-0123', status: 'active', created_at: '2026-01-04T00:00:00Z', updated_at: '2026-01-04T00:00:00Z' },
  { id: 2, name: 'Lee Jordan', business_name: null, email: null, phone: '555-0199', status: 'archived', created_at: '2026-01-05T00:00:00Z', updated_at: '2026-01-05T00:00:00Z' },
]
const linkStub = { props: ['to'], template: '<a><slot /></a>' }
const mountOptions = { global: { stubs: { RouterLink: linkStub } } }

beforeEach(() => vi.clearAllMocks())
afterEach(() => vi.restoreAllMocks())

describe('customer directory page', () => {
  it('loads active customers by default and filters visible results by search', async () => {
    vi.mocked(listCustomers).mockResolvedValue([customers[0]])
    const wrapper = mount(CustomerListPage, mountOptions)
    await flushPromises()
    expect(listCustomers).toHaveBeenCalledWith(false)
    expect(wrapper.text()).toContain('Casey Morgan')

    await wrapper.get('#customer-search').setValue('copper peak')
    await new Promise((resolve) => setTimeout(resolve, 200))
    await flushPromises()
    expect(wrapper.text()).toContain('Casey Morgan')

    await wrapper.get('#customer-search').setValue('no match')
    await new Promise((resolve) => setTimeout(resolve, 200))
    await flushPromises()
    expect(wrapper.text()).toContain('No matching customers')
  })

  it('requests archived records for the archived and all filters', async () => {
    vi.mocked(listCustomers).mockResolvedValue(customers)
    const wrapper = mount(CustomerListPage, mountOptions)
    await flushPromises()
    await wrapper.get('button[aria-pressed="false"]:nth-child(2)').trigger('click')
    await flushPromises()
    expect(listCustomers).toHaveBeenLastCalledWith(true)
    expect(wrapper.text()).toContain('Lee Jordan')
    expect(wrapper.text()).not.toContain('Casey Morgan')

    await wrapper.get('button[aria-pressed="false"]:nth-child(3)').trigger('click')
    await flushPromises()
    expect(listCustomers).toHaveBeenLastCalledWith(true)
    expect(wrapper.text()).toContain('Casey Morgan')
    expect(wrapper.text()).toContain('Lee Jordan')
  })

  it('shows the loading error and retries the list request', async () => {
    vi.mocked(listCustomers).mockRejectedValueOnce(new Error('Temporary network issue')).mockResolvedValueOnce([])
    const wrapper = mount(CustomerListPage, mountOptions)
    await flushPromises()
    expect(wrapper.text()).toContain('Temporary network issue')
    await wrapper.get('.directory-state button').trigger('click')
    await flushPromises()
    expect(listCustomers).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('No active customers yet')
  })
})
