import http from '../../api/http'
import type { Diagnostic, DiagnosticCreatePayload } from './types'

export async function listCustomerDiagnostics(customerId: number): Promise<Diagnostic[]> {
  const response = await http.get<Diagnostic[]>(`/customers/${customerId}/diagnostics`)
  return response.data
}

export async function createCustomerDiagnostic(
  customerId: number,
  payload: DiagnosticCreatePayload,
): Promise<Diagnostic> {
  const response = await http.post<Diagnostic>(`/customers/${customerId}/diagnostics`, payload)
  return response.data
}
