import type { FormInstance } from 'antd'
import type { AdminScope, OAuthClient } from '../../../lib/types'

export interface ClientFormValues {
  name: string
  redirect_uris_text: string
  allowed_scopes: string[]
  is_active: boolean
  require_pkce: boolean
}

export interface PendingTwoFactorAction {
  title: string
  description: string
  run: (code?: string) => Promise<void>
}

export interface ClientFormModalProps {
  open: boolean
  editingClient: OAuthClient | null
  saving: boolean
  isMobile: boolean
  scopes: AdminScope[]
  form: FormInstance<ClientFormValues>
  onOk: () => void
  onCancel: () => void
}
