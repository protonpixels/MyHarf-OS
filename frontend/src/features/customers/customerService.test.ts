import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../api/http', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))

import http from '../../api/http'
import { archiveCustomer, createCustomer, getCustomer, listCustomers, updateCustomer } from './customerService'
import type { Customer, CustomerPayload } from './types'

const customer: Customer = {
  id: 4,
  name: 'Taylor Smith',
  business_name: null,
  email: null,
  phone: null,
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}
const payload: CustomerPayload = { name: customer.name, business_name: null, email: null, phone: null }

describe('customer API service', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists customers using only the include_archived query supported by the API', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: [customer] } as never)
    await expect(listCustomers()).resolves.toEqual([customer])
    expect(http.get).toHaveBeenCalledWith('/customers', { params: { include_archived: false } })
    await listCustomers(true)
    expect(http.get).toHaveBeenLastCalledWith('/customers', { params: { include_archived: true } })
  })

  it('retrieves, creates, updates, and archives through the matching REST methods and payloads', async () => {
    vi.mocked(http.get).mockResolvedValue({ data: customer } as never)
    vi.mocked(http.post).mockResolvedValue({ data: customer } as never)
    vi.mocked(http.patch).mockResolvedValue({ data: customer } as never)
    vi.mocked(http.delete).mockResolvedValue({ data: { ...customer, status: 'archived' } } as never)

    await expect(getCustomer(4)).resolves.toEqual(customer)
    await createCustomer(payload)
    await updateCustomer(4, payload)
    await archiveCustomer(4)

    expect(http.get).toHaveBeenCalledWith('/customers/4')
    expect(http.post).toHaveBeenCalledWith('/customers', payload)
    expect(http.patch).toHaveBeenCalledWith('/customers/4', payload)
    expect(http.delete).toHaveBeenCalledWith('/customers/4')
  })
})
