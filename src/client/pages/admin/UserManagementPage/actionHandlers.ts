import type { AdminUser, AdminUserCreatePayload } from '../../../lib/types'
import type { FormInstance } from 'antd'
import type { MessageInstance } from 'antd/es/message/interface'
import type { TwoFactorDialogState } from './types'
import { resolveErrorMessage } from './utils'
import { buildUpdatePayload, isPasswordMismatch } from './formHelpers'

export async function handleSave(params: {
  editingUser: AdminUser | null
  editForm: FormInstance
  message: MessageInstance
  setSaving: (saving: boolean) => void
  setUsers: (updater: (prev: AdminUser[]) => AdminUser[]) => void
  setTwoFactorDialog: (dialog: TwoFactorDialogState | null) => void
  closeEditModal: () => void
  currentUser: { two_factor_enabled?: boolean } | null
  openTwoFactorDialog: (title: string, description: string, onConfirm: (code: string) => Promise<void>) => void
}) {
  const { editingUser, editForm, message, setSaving, setUsers, setTwoFactorDialog, closeEditModal, currentUser, openTwoFactorDialog } = params
  if (!editingUser) return
  try {
    const values = await editForm.validateFields()
    const payload = buildUpdatePayload(values, editingUser)

    if (Object.keys(payload).length === 0) {
      message.info('没有需要保存的改动')
      closeEditModal()
      return
    }

    const performSave = async (twoFactorCode?: string) => {
      setSaving(true)
      try {
        const { updateUser } = await import('../../../lib/admin')
        const updated = await updateUser(editingUser.id, payload, twoFactorCode)
        setUsers((prev: AdminUser[]) => prev.map((item: AdminUser) => (item.id === editingUser.id ? updated : item)))
        message.success('用户信息已更新')
        closeEditModal()
        setTwoFactorDialog(null)
      } finally { setSaving(false) }
    }

    if (currentUser?.two_factor_enabled) {
      openTwoFactorDialog('二步验证后保存用户', '管理员写操作属于危险操作，请先完成二步验证再保存本次修改。', async (code: string) => {
      try { await performSave(code) } catch (err: unknown) { message.error(resolveErrorMessage(err)) }
        })
        return
      }
      await performSave()
    } catch (err: unknown) {
      if (typeof err === 'object' && err && 'errorFields' in err) return
      message.error(resolveErrorMessage(err))
    }
}

export async function handleResetPassword(params: {
  resettingUser: AdminUser | null
  resetPasswordForm: FormInstance
  message: MessageInstance
  setResettingPassword: (resetting: boolean) => void
  setUsers: (updater: (prev: AdminUser[]) => AdminUser[]) => void
  setTwoFactorDialog: (dialog: TwoFactorDialogState | null) => void
  closeResetPasswordModal: () => void
  currentUser: { two_factor_enabled?: boolean } | null
  openTwoFactorDialog: (title: string, description: string, onConfirm: (code: string) => Promise<void>) => void
}) {
  const { resettingUser, resetPasswordForm, message, setResettingPassword, setUsers, setTwoFactorDialog, closeResetPasswordModal, currentUser, openTwoFactorDialog } = params
  if (!resettingUser) return
  try {
    const values = await resetPasswordForm.validateFields()
    const performReset = async (twoFactorCode?: string) => {
      setResettingPassword(true)
      try {
        const { updateUser } = await import('../../../lib/admin')
        const updated = await updateUser(resettingUser.id, { password: values.password }, twoFactorCode)
        setUsers((prev: AdminUser[]) => prev.map((item: AdminUser) => (item.id === resettingUser.id ? updated : item)))
        message.success(`已重置用户 ${resettingUser.username} 的密码`)
        closeResetPasswordModal()
        setTwoFactorDialog(null)
      } finally { setResettingPassword(false) }
    }

    if (currentUser?.two_factor_enabled) {
      openTwoFactorDialog('二步验证后重置密码', '管理员重置他人密码属于危险操作，请先完成二步验证。', async (code: string) => {
        try { await performReset(code) } catch (err: unknown) { message.error(resolveErrorMessage(err)) }
      })
      return
    }
    await performReset()
  } catch (err: unknown) {
    if (typeof err === 'object' && err && 'errorFields' in err) return
    message.error(resolveErrorMessage(err))
  }
}

export async function handleDeleteUser(params: {
  deletingUser: AdminUser | null
  deleteForm: FormInstance
  editingUser: AdminUser | null
  message: MessageInstance
  setDeleting: (deleting: boolean) => void
  setUsers: (updater: (prev: AdminUser[]) => AdminUser[]) => void
  setTwoFactorDialog: (dialog: TwoFactorDialogState | null) => void
  closeDeleteModal: () => void
  closeEditModal: () => void
  currentUser: { two_factor_enabled?: boolean } | null
  openTwoFactorDialog: (title: string, description: string, onConfirm: (code: string) => Promise<void>) => void
}) {
  const { deletingUser, deleteForm, editingUser, message, setDeleting, setUsers, setTwoFactorDialog, closeDeleteModal, closeEditModal, currentUser, openTwoFactorDialog } = params
  if (!deletingUser) return
  try {
    await deleteForm.validateFields()
    const performDelete = async (twoFactorCode?: string) => {
      setDeleting(true)
      try {
        const { deleteUser } = await import('../../../lib/admin')
        await deleteUser(deletingUser.id, twoFactorCode)
        setUsers((prev: AdminUser[]) => prev.filter((item: AdminUser) => item.id !== deletingUser.id))
        if (editingUser?.id === deletingUser.id) closeEditModal()
        message.success(`已删除用户 ${deletingUser.username}`)
        closeDeleteModal()
        setTwoFactorDialog(null)
      } finally { setDeleting(false) }
    }

    if (currentUser?.two_factor_enabled) {
      openTwoFactorDialog('二步验证后删除用户', '删除用户属于危险操作，请先完成二步验证再继续。', async (code: string) => {
      try { await performDelete(code) } catch (err: unknown) { message.error(resolveErrorMessage(err)) }
        })
        return
      }
      await performDelete()
    } catch (err: unknown) {
      if (typeof err === 'object' && err && 'errorFields' in err) return
      message.error(resolveErrorMessage(err))
    }
}

export async function handleCreate(params: {
  createForm: FormInstance
  message: MessageInstance
  setCreating: (creating: boolean) => void
  setUsers: (updater: (prev: AdminUser[]) => AdminUser[]) => void
  setTwoFactorDialog: (dialog: TwoFactorDialogState | null) => void
  closeCreateModal: () => void
  currentUser: { two_factor_enabled?: boolean } | null
  openTwoFactorDialog: (title: string, description: string, onConfirm: (code: string) => Promise<void>) => void
}) {
  const { createForm, message, setCreating, setUsers, setTwoFactorDialog, closeCreateModal, currentUser, openTwoFactorDialog } = params
  try {
    const values = await createForm.validateFields()
    if (isPasswordMismatch(values)) {
      message.error('两次输入的密码不一致')
      return
    }
    const payload: AdminUserCreatePayload = {
      username: values.username.trim(),
      email: values.email.trim().toLowerCase(),
      name: values.name?.trim() || null,
      role: values.role,
      status: values.status,
      password: values.password,
    }

    const performCreate = async (twoFactorCode?: string) => {
      setCreating(true)
      try {
        const { createUser } = await import('../../../lib/admin')
        const created = await createUser(payload, twoFactorCode)
        setUsers((prev: AdminUser[]) => [created, ...prev])
        message.success(`已创建用户 ${created.username}`)
        closeCreateModal()
        setTwoFactorDialog(null)
      } finally { setCreating(false) }
    }

    if (currentUser?.two_factor_enabled) {
      openTwoFactorDialog('二步验证后创建用户', '管理员创建用户属于危险操作，请先完成二步验证。', async (code: string) => {
      try { await performCreate(code) } catch (err: unknown) { message.error(resolveErrorMessage(err)) }
        })
        return
      }
      await performCreate()
    } catch (err: unknown) {
      if (typeof err === 'object' && err && 'errorFields' in err) return
      message.error(resolveErrorMessage(err))
    }
  }
