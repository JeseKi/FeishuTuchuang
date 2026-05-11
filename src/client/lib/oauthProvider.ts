import api, { buildTwoFactorHeaders } from './api'
import type {
  OAuthAuthorizeConfirmPayload,
  OAuthAuthorizeMetadata,
  OAuthAuthorizeResult,
  OAuthClient,
  OAuthClientCreatePayload,
  OAuthClientUpdatePayload,
  OAuthClientWithSecret,
  OAuthDeviceAuthorizationConfirmPayload,
  OAuthDeviceAuthorizationMetadata,
  OAuthDeviceAuthorizationResult,
} from './types'

export async function fetchOAuthAuthorizeMetadata(params: URLSearchParams): Promise<OAuthAuthorizeMetadata> {
  const { data } = await api.get<OAuthAuthorizeMetadata>('/oauth-provider/authorize/metadata', {
    params: Object.fromEntries(params.entries()),
  })
  return data
}

export async function confirmOAuthAuthorize(
  payload: OAuthAuthorizeConfirmPayload,
): Promise<OAuthAuthorizeResult> {
  const { data } = await api.post<OAuthAuthorizeResult>('/oauth-provider/authorize', payload)
  return data
}

export async function fetchOAuthDeviceAuthorizationMetadata(
  userCode: string,
): Promise<OAuthDeviceAuthorizationMetadata> {
  const { data } = await api.get<OAuthDeviceAuthorizationMetadata>('/oauth-provider/device/metadata', {
    params: { user_code: userCode },
  })
  return data
}

export async function confirmOAuthDeviceAuthorization(
  payload: OAuthDeviceAuthorizationConfirmPayload,
): Promise<OAuthDeviceAuthorizationResult> {
  const { data } = await api.post<OAuthDeviceAuthorizationResult>('/oauth-provider/device/authorize', payload)
  return data
}

export async function listOAuthClients(): Promise<OAuthClient[]> {
  const { data } = await api.get<OAuthClient[]>('/oauth-provider/clients')
  return data
}

export async function createOAuthClient(
  payload: OAuthClientCreatePayload,
  twoFactorCode?: string,
): Promise<OAuthClientWithSecret> {
  const { data } = await api.post<OAuthClientWithSecret>('/oauth-provider/clients', payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function updateOAuthClient(
  clientId: string,
  payload: OAuthClientUpdatePayload,
  twoFactorCode?: string,
): Promise<OAuthClient> {
  const { data } = await api.patch<OAuthClient>(`/oauth-provider/clients/${clientId}`, payload, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function deleteOAuthClient(clientId: string, twoFactorCode?: string): Promise<void> {
  await api.delete(`/oauth-provider/clients/${clientId}`, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
}

export async function resetOAuthClientSecret(
  clientId: string,
  twoFactorCode?: string,
): Promise<OAuthClientWithSecret> {
  const { data } = await api.post<OAuthClientWithSecret>(
    `/oauth-provider/clients/${clientId}/secret`,
    null,
    { headers: buildTwoFactorHeaders(twoFactorCode) },
  )
  return data
}
