import http from '../../api/http'
import type { Customer, CustomerPayload } from './types'

export async function listCustomers(includeArchived = false): Promise<Customer[]> {
  const response = await http.get<Customer[]>('/customers', {
    params: { include_archived: includeArchived },
  })
  return response.data
}

export async function getCustomer(customerId: number): Promise<Customer> {
  const response = await http.get<Customer>(`/customers/${customerId}`)
  return response.data
}

export async function createCustomer(payload: CustomerPayload): Promise<Customer> {
  const response = await http.post<Customer>('/customers', payload)
  return response.data
}

export async function updateCustomer(customerId: number, payload: CustomerPayload): Promise<Customer> {
  const response = await http.patch<Customer>(`/customers/${customerId}`, payload)
  return response.data
}

export async function archiveCustomer(customerId: number): Promise<Customer> {
  const response = await http.delete<Customer>(`/customers/${customerId}`)
  return response.data
}
