import api from './api'

export interface ApiKey {
  id: number
  name: string
  key_prefix: string
  scopes: string[]
  expires_at?: string | null
  last_used_at?: string | null
  revoked_at?: string | null
  created_at: string
}

export interface ApiKeyCreateResult extends ApiKey {
  key: string
}

export interface ApiKeyCreatePayload {
  name: string
  scopes?: string[]
  expires_at?: string | null
}

export async function listApiKeys(): Promise<ApiKey[]> {
  const response = await api.get<ApiKey[]>('/auth/api-keys')
  return response.data
}

export async function createApiKey(payload: ApiKeyCreatePayload): Promise<ApiKeyCreateResult> {
  const response = await api.post<ApiKeyCreateResult>('/auth/api-keys', payload)
  return response.data
}

export async function revokeApiKey(id: number): Promise<void> {
  await api.delete(`/auth/api-keys/${id}`)
}

