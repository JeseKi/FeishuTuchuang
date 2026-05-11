import api, { buildTwoFactorHeaders } from './api'
import type {
  AdminScope,
  AdminScopeUpdatePayload,
  AdminUser,
  AdminUserCreatePayload,
  AdminUserScopesUpdatePayload,
  AdminUserUpdatePayload,
} from './types'

export async function createUser(
  payload: AdminUserCreatePayload,
  twoFactorCode?: string,
): Promise<AdminUser> {
  const { data } = await api.post<AdminUser>('/admin/users', payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function listUsers(): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>('/admin/users')
  return data
}

export async function updateUser(
  userId: number,
  payload: AdminUserUpdatePayload,
  twoFactorCode?: string,
): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${userId}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function deleteUser(userId: number, twoFactorCode?: string): Promise<void> {
  await api.delete(`/admin/users/${userId}`, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
}

export async function listScopes(): Promise<AdminScope[]> {
  const { data } = await api.get<AdminScope[]>('/admin/scopes')
  return data
}

export async function updateScope(
  scope: string,
  payload: AdminScopeUpdatePayload,
  twoFactorCode?: string,
): Promise<AdminScope> {
  const { data } = await api.patch<AdminScope>(`/admin/scopes/${encodeURIComponent(scope)}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function updateUserScopes(
  userId: number,
  payload: AdminUserScopesUpdatePayload,
  twoFactorCode?: string,
): Promise<AdminUser> {
  const { data } = await api.put<AdminUser>(`/admin/users/${userId}/scopes`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}
