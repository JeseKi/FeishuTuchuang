import type { OAuthClient } from '../../../lib/types'
import type { ClientFormValues } from './types'

export function formatRedirectUris(values: string[]): string {
  return values.join('\n')
}

export function parseRedirectUris(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function buildFormValues(client?: OAuthClient): ClientFormValues {
  return {
    name: client?.name ?? '',
    redirect_uris_text: client ? formatRedirectUris(client.redirect_uris) : '',
    allowed_scopes: client?.allowed_scopes ?? [],
    is_active: client?.is_active ?? true,
    require_pkce: client?.require_pkce ?? true,
  }
}
