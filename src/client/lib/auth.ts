import api, { buildTwoFactorHeaders } from './api'
import { setTokens, clearTokens } from './tokenStorage'
import type {
  BackupCodesResponse,
  EmailChangeCodePayload,
  EmailChangeConfirmPayload,
  LoginResponse,
  LoginPayload,
  MessageResponse,
  OAuthProviderInfo,
  OAuthProvidersResponse,
  OAuthTicketExchangePayload,
  PasswordChangeConfirmPayload,
  PasswordResetLinkPayload,
  PasswordResetWithTokenPayload,
  RegisterWithCodePayload,
  TokenResponse,
  TwoFactorDisablePayload,
  TwoFactorRegenerateBackupCodesPayload,
  TwoFactorSetupConfirmPayload,
  TwoFactorSetupStartResponse,
  TwoFactorVerifyPayload,
  UpdateProfilePayload,
  UserProfile,
  VerificationCodePayload,
} from './types'

function cleanupBaseUrl(url: string | undefined): string {
  if (!url) {
    return ''
  }
  if (url.endsWith('/')) {
    return url.slice(0, -1)
  }
  return url
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  console.log('【Auth API】准备发送登录请求', { 登录标识: payload.username })
  const { data } = await api.post<LoginResponse>('/auth/login', payload)
  if ('access_token' in data) {
    console.log('【Auth API】登录请求返回', { tokenType: data.token_type })
    setTokens(data.access_token)
  }
  return data
}

export async function fetchOAuthProviders(): Promise<OAuthProviderInfo[]> {
  const { data } = await api.get<OAuthProvidersResponse>('/oauth/providers')
  return data.providers
}

export async function exchangeOAuthTicket(payload: OAuthTicketExchangePayload): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/oauth/ticket', payload)
  if ('access_token' in data) {
    setTokens(data.access_token)
  }
  return data
}

export function buildOAuthAuthorizeUrl(provider: OAuthProviderInfo['provider'], redirectPath?: string): string {
  const baseUrl = cleanupBaseUrl(import.meta.env.VITE_API_BASE_URL ?? '/api')
  const providerPathMap: Record<OAuthProviderInfo['provider'], string> = {
    GITHUB: 'github',
    GOOGLE: 'google',
  }
  const params = new URLSearchParams()
  if (redirectPath) {
    params.set('redirect_path', redirectPath)
  }
  const query = params.toString()
  return `${baseUrl}/oauth/${providerPathMap[provider]}/authorize${query ? `?${query}` : ''}`
}

export async function verifyTwoFactorLogin(payload: TwoFactorVerifyPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/2fa/verify', payload)
  setTokens(data.access_token)
  return data
}

export async function register(payload: RegisterWithCodePayload): Promise<UserProfile> {
  const { data } = await api.post<UserProfile>('/auth/register', payload)
  return data
}

export async function sendVerificationCode(payload: VerificationCodePayload): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/send-verification-code', payload)
  return data
}

export async function sendPasswordResetLink(payload: PasswordResetLinkPayload): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/forgot-password/link', payload)
  return data
}

export async function registerWithCode(payload: RegisterWithCodePayload): Promise<UserProfile> {
  const { data } = await api.post<UserProfile>('/auth/register-with-code', payload)
  return data
}

export async function fetchProfile(): Promise<UserProfile> {
  const { data } = await api.get<UserProfile>('/auth/profile')
  return data
}

export async function updateProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  const { data } = await api.put<UserProfile>('/auth/profile', payload)
  return data
}

export async function sendEmailChangeCode(payload: EmailChangeCodePayload): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/profile/email-change/code', payload)
  return data
}

export async function resetPasswordWithToken(payload: PasswordResetWithTokenPayload): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/forgot-password/reset', payload)
  return data
}

export async function confirmEmailChange(payload: EmailChangeConfirmPayload): Promise<UserProfile> {
  const { data } = await api.post<UserProfile>('/auth/profile/email-change/confirm', payload)
  return data
}

export async function sendPasswordChangeLink(twoFactorCode?: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/profile/password-change/link', null, {
    headers: buildTwoFactorHeaders(twoFactorCode),
  })
  return data
}

export async function confirmPasswordChange(payload: PasswordChangeConfirmPayload): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/profile/password-change/confirm', payload)
  return data
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout')
  } finally {
    clearTokens()
  }
}

export async function logoutAllDevices(): Promise<MessageResponse> {
  try {
    const { data } = await api.post<MessageResponse>('/auth/logout-all')
    return data
  } finally {
    clearTokens()
  }
}

export async function startTwoFactorSetup(): Promise<TwoFactorSetupStartResponse> {
  const { data } = await api.post<TwoFactorSetupStartResponse>('/auth/2fa/setup/start')
  return data
}

export async function confirmTwoFactorSetup(payload: TwoFactorSetupConfirmPayload): Promise<BackupCodesResponse> {
  const { data } = await api.post<BackupCodesResponse>('/auth/2fa/setup/confirm', payload)
  return data
}

export async function disableTwoFactor(payload: TwoFactorDisablePayload): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/auth/2fa/disable', payload)
  clearTokens()
  return data
}

export async function regenerateBackupCodes(
  payload: TwoFactorRegenerateBackupCodesPayload,
): Promise<BackupCodesResponse> {
  const { data } = await api.post<BackupCodesResponse>('/auth/2fa/backup-codes/regenerate', payload)
  return data
}

export function clearAuthState(): void {
  clearTokens()
}
