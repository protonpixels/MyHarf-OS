export type CustomerStatus = 'active' | 'archived'

export interface Customer {
  id: number
  name: string
  business_name: string | null
  email: string | null
  phone: string | null
  status: CustomerStatus
  created_at: string
  updated_at: string
}

export interface CustomerPayload {
  name: string
  business_name: string | null
  email: string | null
  phone: string | null
}

export type CustomerStatusFilter = 'active' | 'archived' | 'all'
