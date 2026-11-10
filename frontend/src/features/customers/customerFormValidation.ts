import type { ApiClientError, ApiIssue } from '../../api/errors'
import type { Customer, CustomerPayload } from './types'

export type CustomerField = keyof CustomerPayload
export type CustomerFieldErrors = Partial<Record<CustomerField, string>>
export interface CustomerFormValues extends Record<CustomerField, string> {}

export const emptyCustomerForm: CustomerFormValues = {
  name: '',
  business_name: '',
  email: '',
  phone: '',
}

export function customerToFormValues(customer?: Customer): CustomerFormValues {
  return {
    name: customer?.name ?? '',
    business_name: customer?.business_name ?? '',
    email: customer?.email ?? '',
    phone: customer?.phone ?? '',
  }
}

export function validateCustomerForm(values: CustomerFormValues): CustomerFieldErrors {
  const errors: CustomerFieldErrors = {}
  const name = values.name.trim()
  const businessName = values.business_name.trim()
  const email = values.email.trim()
  const phone = values.phone.trim()

  if (!name) errors.name = 'Enter a customer name.'
  else if (name.length > 200) errors.name = 'Name must be 200 characters or fewer.'
  if (businessName.length > 200) errors.business_name = 'Business name must be 200 characters or fewer.'
  if (email.length > 320) errors.email = 'Email must be 320 characters or fewer.'
  else if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) errors.email = 'Enter an email address in a valid format.'
  if (phone.length > 50) errors.phone = 'Phone must be 50 characters or fewer.'
  return errors
}

export function normalizeCustomerForm(values: CustomerFormValues): CustomerPayload {
  const optional = (value: string) => value.trim() || null
  return {
    name: values.name.trim(),
    business_name: optional(values.business_name),
    email: optional(values.email),
    phone: optional(values.phone),
  }
}

export function mapCustomerApiIssues(issues: ApiIssue[]): { fieldErrors: CustomerFieldErrors; generalErrors: string[] } {
  const fieldErrors: CustomerFieldErrors = {}
  const generalErrors: string[] = []
  const fields: CustomerField[] = ['name', 'business_name', 'email', 'phone']

  for (const issue of issues) {
    const field = issue.location?.find((part): part is CustomerField =>
      typeof part === 'string' && fields.includes(part as CustomerField),
    )
    if (field && !fieldErrors[field]) fieldErrors[field] = issue.message
    else if (!field) generalErrors.push(issue.message)
  }
  return { fieldErrors, generalErrors }
}

export function customerErrorMessages(error: unknown): { fieldErrors: CustomerFieldErrors; generalErrors: string[] } {
  if (error instanceof Error && 'issues' in error) {
    const apiError = error as ApiClientError
    if (apiError.issues.length === 0) return { fieldErrors: {}, generalErrors: [apiError.message] }
    return mapCustomerApiIssues(apiError.issues)
  }
  return {
    fieldErrors: {},
    generalErrors: [error instanceof Error ? error.message : 'We couldn’t save this customer. Please try again.'],
  }
}
