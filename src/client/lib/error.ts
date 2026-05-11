import { isAxiosError } from 'axios'

interface PermissionErrorDetail {
  message?: string
  required_scopes?: unknown
  missing_scopes?: unknown
}

function normalizeScopes(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
}

function resolveStructuredErrorMessage(detail: unknown): string | null {
  if (!detail || typeof detail !== 'object') {
    return null
  }

  const normalizedDetail = detail as PermissionErrorDetail

  if (typeof normalizedDetail.message === 'string' && normalizedDetail.message.length > 0) {
    return normalizedDetail.message
  }

  const missingScopes = normalizeScopes(normalizedDetail.missing_scopes)
  if (missingScopes.length > 0) {
    return `缺少所需权限: ${missingScopes.join(', ')}`
  }

  const requiredScopes = normalizeScopes(normalizedDetail.required_scopes)
  if (requiredScopes.length > 0) {
    return `缺少所需权限: ${requiredScopes.join(', ')}`
  }

  return null
}

function resolvePayloadMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  const maybePayload = payload as {
    message?: unknown
    detail?: unknown
  }

  if (typeof maybePayload.message === 'string' && maybePayload.message.length > 0) {
    return maybePayload.message
  }

  if (typeof maybePayload.detail === 'string' && maybePayload.detail.length > 0) {
    return maybePayload.detail
  }

  return resolveStructuredErrorMessage(maybePayload.detail)
}

export function resolveApiErrorMessage(
  error: unknown,
  fallback = '请求失败，请稍后重试。',
): string {
  if (isAxiosError(error)) {
    return resolvePayloadMessage(error.response?.data) ?? fallback
  }

  if (error instanceof Error) {
    return error.message
  }

  return fallback
}

