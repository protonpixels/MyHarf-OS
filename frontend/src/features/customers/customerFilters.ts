import type { Customer, CustomerStatusFilter } from './types'

export function filterCustomers(
  customers: Customer[],
  statusFilter: CustomerStatusFilter,
  searchTerm: string,
): Customer[] {
  const normalizedSearch = searchTerm.trim().toLocaleLowerCase()

  return customers.filter((customer) => {
    const matchesStatus = statusFilter === 'all' || customer.status === statusFilter
    if (!matchesStatus) return false
    if (!normalizedSearch) return true

    return [customer.name, customer.business_name, customer.email, customer.phone]
      .some((value) => value?.toLocaleLowerCase().includes(normalizedSearch))
  })
}
