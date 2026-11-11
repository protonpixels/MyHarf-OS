import http from '../../api/http'
import type { Finding, FindingCreatePayload, FindingUpdatePayload } from './types'

export async function listDiagnosticFindings(diagnosticId: number): Promise<Finding[]> {
  const response = await http.get<Finding[]>(`/diagnostics/${diagnosticId}/findings`)
  return response.data
}

export async function getFinding(findingId: number): Promise<Finding> {
  const response = await http.get<Finding>(`/findings/${findingId}`)
  return response.data
}

export async function createFinding(
  diagnosticId: number,
  payload: FindingCreatePayload,
): Promise<Finding> {
  const response = await http.post<Finding>(`/diagnostics/${diagnosticId}/findings`, payload)
  return response.data
}

export async function updateFinding(
  findingId: number,
  payload: FindingUpdatePayload,
): Promise<Finding> {
  const response = await http.patch<Finding>(`/findings/${findingId}`, payload)
  return response.data
}

export async function archiveFinding(findingId: number): Promise<Finding> {
  const response = await http.delete<Finding>(`/findings/${findingId}`)
  return response.data
}
