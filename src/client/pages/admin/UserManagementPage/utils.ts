import type { UserRole, UserStatus } from '../../../lib/types'
import { resolveApiErrorMessage } from '../../../lib/error'

export function resolveErrorMessage(error: unknown): string {
  return resolveApiErrorMessage(error, '请求失败，请稍后再试。')
}

export const roleOptions = [
  { value: 'admin' as UserRole, label: '管理员' },
  { value: 'user' as UserRole, label: '普通用户' },
]

export const statusOptions = [
  { value: 'active' as UserStatus, label: '启用' },
  { value: 'inactive' as UserStatus, label: '停用' },
]
