import http from '../../api/http'
import type { Diagnostic, DiagnosticCreatePayload, DiagnosticUpdatePayload } from './types'

export async function getDiagnostic(diagnosticId: number): Promise<Diagnostic> {
  const response = await http.get<Diagnostic>(`/diagnostics/${diagnosticId}`)
  return response.data
}

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

export async function updateDiagnostic(
  diagnosticId: number,
  payload: DiagnosticUpdatePayload,
): Promise<Diagnostic> {
  const response = await http.patch<Diagnostic>(`/diagnostics/${diagnosticId}`, payload)
  return response.data
}

export async function archiveDiagnostic(diagnosticId: number): Promise<Diagnostic> {
  const response = await http.delete<Diagnostic>(`/diagnostics/${diagnosticId}`)
  return response.data
}
