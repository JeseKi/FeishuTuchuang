import type { UserRole, UserStatus } from '../../../lib/types'

export interface EditFormValues {
  username: string
  email: string
  name?: string | null
  role: UserRole
  status: UserStatus
}

export interface ResetPasswordFormValues {
  password: string
  confirmPassword: string
  confirmationText: string
}

export interface DeleteUserFormValues {
  confirmationText: string
}

export interface CreateFormValues {
  username: string
  email: string
  name?: string | null
  role: UserRole
  status: UserStatus
  password: string
  confirmPassword: string
}

export interface TwoFactorDialogState {
  title: string
  description: string
  onConfirm: (code: string) => Promise<void>
}
