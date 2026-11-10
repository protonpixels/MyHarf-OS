import { describe, expect, it } from 'vitest'
import { filterCustomers } from './customerFilters'
import type { Customer } from './types'

const records: Customer[] = [
  { id: 1, name: 'Morgan Lee', business_name: 'Peak Roofing', email: 'morgan@peak.example', phone: '555-0101', status: 'active', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
  { id: 2, name: 'Sam Rivera', business_name: null, email: null, phone: '555-0202', status: 'archived', created_at: '2026-01-02T00:00:00Z', updated_at: '2026-01-02T00:00:00Z' },
]

describe('customer directory filtering', () => {
  it('filters active, archived, and all statuses', () => {
    expect(filterCustomers(records, 'active', '')).toEqual([records[0]])
    expect(filterCustomers(records, 'archived', '')).toEqual([records[1]])
    expect(filterCustomers(records, 'all', '')).toEqual(records)
  })

  it.each(['morgan', 'peak roof', 'morgan@peak.example', '555-0101'])(
    'searches customer name, business, email, and phone with case-insensitive matching (%s)',
    (term) => expect(filterCustomers(records, 'all', term)).toEqual([records[0]]),
  )

  it('trims the search term and returns an empty result when there are no matches', () => {
    expect(filterCustomers(records, 'all', '  RIVERA ')).toEqual([records[1]])
    expect(filterCustomers(records, 'active', 'nobody')).toEqual([])
  })
})
