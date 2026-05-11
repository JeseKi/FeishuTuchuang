import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'
import { clearTokens, getAccessToken, setTokens } from './tokenStorage'
import type { TokenResponse } from './types'

export const TWO_FACTOR_CODE_HEADER = 'X-2FA-Code'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  withCredentials: true,
})

let refreshRequest: Promise<string | null> | null = null

function cleanupBaseUrl(url: string | undefined): string {
  if (!url) {
    return ''
  }
  if (url.endsWith('/')) {
    return url.slice(0, -1)
  }
  return url
}

function shouldSkipRefresh(url?: string): boolean {
  if (!url) {
    return false
  }
  const blocked = [
    '/auth/login',
    '/auth/register',
    '/auth/register-with-code',
    '/auth/send-verification-code',
    '/auth/forgot-password/link',
    '/auth/forgot-password/reset',
    '/auth/2fa/verify',
    '/auth/profile/password-change/confirm',
    '/auth/refresh',
  ]
  return blocked.some((path) => url.includes(path))
}

async function requestRefreshToken(): Promise<string | null> {
  if (!getAccessToken()) {
    return null
  }

  const baseUrl = cleanupBaseUrl(api.defaults.baseURL)
  try {
    const response = await axios.post<TokenResponse>(
      `${baseUrl}/auth/refresh`,
      null,
      {
        withCredentials: true,
      },
    )

    const { access_token: accessToken } = response.data
    setTokens(accessToken)
    return accessToken
  } catch (error) {
    clearTokens()
    throw error
  }
}

type RetryableConfig = AxiosRequestConfig & { _retry?: boolean }

export function buildTwoFactorHeaders(code?: string): Record<string, string> | undefined {
  const normalizedCode = code?.trim()
  if (!normalizedCode) {
    return undefined
  }
  return {
    [TWO_FACTOR_CODE_HEADER]: normalizedCode,
  }
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const originalRequest = error.config as RetryableConfig | undefined

    if (status === 401 && originalRequest && !originalRequest._retry && !shouldSkipRefresh(originalRequest.url)) {
      originalRequest._retry = true

      try {
        refreshRequest = refreshRequest ?? requestRefreshToken()
        const newAccessToken = await refreshRequest
        refreshRequest = null

        if (!newAccessToken) {
          throw error
        }

        originalRequest.headers = originalRequest.headers ?? {}
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return api(originalRequest)
      } catch (refreshError) {
        refreshRequest = null
        clearTokens()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export default api
