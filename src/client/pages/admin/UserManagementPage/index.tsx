import { Alert, App, Button, Card, Flex, Form, Input, Space, Table, Typography } from 'antd'
import { ReloadOutlined, TeamOutlined, UserAddOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { listUsers } from '../../../lib/admin'
import type { AdminUser } from '../../../lib/types'
import { useAuth } from '../../../hooks/useAuth'
import DangerousActionTwoFactorModal from '../../../components/auth/DangerousActionTwoFactorModal'
import { resolveErrorMessage } from './utils'
import type { TwoFactorDialogState } from './types'
import EditUserModal from './EditUserModal'
import ResetPasswordModal from './ResetPasswordModal'
import DeleteUserModal from './DeleteUserModal'
import CreateUserModal from './CreateUserModal'
import { useColumns } from './columns'
import { buildEditFormValues, buildCreateFormValues } from './formHelpers'
import { handleSave, handleResetPassword, handleDeleteUser, handleCreate } from './actionHandlers'

export default function UserManagementPage() {
  const { message } = App.useApp()
  const { user: currentUser } = useAuth()
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [keyword, setKeyword] = useState('')
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [saving, setSaving] = useState(false)
  const [resettingUser, setResettingUser] = useState<AdminUser | null>(null)
  const [resettingPassword, setResettingPassword] = useState(false)
  const [deletingUser, setDeletingUser] = useState<AdminUser | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [twoFactorDialog, setTwoFactorDialog] = useState<TwoFactorDialogState | null>(null)
  const [editForm] = Form.useForm()
  const [resetPasswordForm] = Form.useForm()
  const [deleteForm] = Form.useForm()
  const [createForm] = Form.useForm()

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listUsers()
      setUsers(data)
    } catch (err) {
      const text = resolveErrorMessage(err)
      setError(text)
      message.error(text)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => { void loadUsers() }, [loadUsers])

  const openEditModal = useCallback((user: AdminUser) => {
    setEditingUser(user)
    editForm.setFieldsValue(buildEditFormValues(user))
  }, [editForm])

  const closeEditModal = useCallback(() => {
    setEditingUser(null)
    editForm.resetFields()
  }, [editForm])

  const openResetPasswordModal = useCallback((user: AdminUser) => {
    setResettingUser(user)
    resetPasswordForm.resetFields()
  }, [resetPasswordForm])

  const closeResetPasswordModal = useCallback(() => {
    setResettingUser(null)
    resetPasswordForm.resetFields()
  }, [resetPasswordForm])

  const closeDeleteModal = useCallback(() => {
    setDeletingUser(null)
    deleteForm.resetFields()
  }, [deleteForm])

  const openTwoFactorDialog = useCallback(
    (title: string, description: string, onConfirm: (code: string) => Promise<void>) => {
      setTwoFactorDialog({ title, description, onConfirm })
    }, [])

  const openCreateModal = useCallback(() => {
    setCreateModalVisible(true)
    createForm.setFieldsValue(buildCreateFormValues())
  }, [createForm])

  const closeCreateModal = useCallback(() => {
    setCreateModalVisible(false)
    createForm.resetFields()
  }, [createForm])

  const filteredUsers = useMemo(() => {
    const trimmed = keyword.trim().toLowerCase()
    if (!trimmed) return users
    return users.filter((user) => {
      const name = user.name ?? ''
      return [user.username, user.email, name].join(' ').toLowerCase().includes(trimmed)
    })
  }, [users, keyword])

  const columns = useColumns({
    currentUserId: currentUser?.id,
    saving,
    deleting,
    editingUserId: editingUser?.id,
    onEdit: openEditModal,
    onDelete: (record) => {
      setDeletingUser(record)
      deleteForm.setFieldsValue({ confirmationText: '' })
    },
    deleteForm,
  })

  return (
    <Flex vertical gap={24}>
      <Card>
        <Flex align={isMobile ? 'stretch' : 'center'} justify="space-between" wrap="wrap" gap={16} vertical={isMobile}>
          <Space>
            <TeamOutlined style={{ fontSize: 20 }} />
            <Typography.Title level={4} style={{ margin: 0 }}>用户管理</Typography.Title>
          </Space>
          <Flex wrap="wrap" gap={8} style={{ width: isMobile ? '100%' : 'auto' }}>
            <Input
              placeholder="搜索用户名 / 邮箱 / 姓名"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              allowClear
              style={{ minWidth: isMobile ? '100%' : 220, flex: isMobile ? 1 : 'auto' }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadUsers} loading={loading}>
              {isMobile ? '' : '刷新'}
            </Button>
            <Button type="primary" icon={<UserAddOutlined />} onClick={openCreateModal} disabled={creating}>
              {isMobile ? '' : '创建用户'}
            </Button>
          </Flex>
        </Flex>
        <Typography.Paragraph type="secondary" className="mt-4">
          在这里可以查看系统内所有用户，并快速调整角色与启用状态。
        </Typography.Paragraph>
      </Card>

      {error && <Alert type="error" showIcon message={error} />}

      <Card bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无用户数据' }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      <EditUserModal
        open={Boolean(editingUser)}
        editingUser={editingUser}
        saving={saving}
        currentUserId={currentUser?.id}
        form={editForm}
        onOk={() => handleSave({
          editingUser,
          editForm,
          message,
          setSaving,
          setUsers,
          setTwoFactorDialog,
          closeEditModal,
          currentUser,
          openTwoFactorDialog,
        })}
        onCancel={closeEditModal}
        onResetPassword={openResetPasswordModal}
      />

      <ResetPasswordModal
        open={Boolean(resettingUser)}
        resettingUser={resettingUser}
        resettingPassword={resettingPassword}
        form={resetPasswordForm}
        onOk={() => handleResetPassword({
          resettingUser,
          resetPasswordForm,
          message,
          setResettingPassword,
          setUsers,
          setTwoFactorDialog,
          closeResetPasswordModal,
          currentUser,
          openTwoFactorDialog,
        })}
        onCancel={closeResetPasswordModal}
      />

      <DeleteUserModal
        open={Boolean(deletingUser)}
        deletingUser={deletingUser}
        deleting={deleting}
        form={deleteForm}
        onOk={() => handleDeleteUser({
          deletingUser,
          deleteForm,
          editingUser,
          message,
          setDeleting,
          setUsers,
          setTwoFactorDialog,
          closeDeleteModal,
          closeEditModal,
          currentUser,
          openTwoFactorDialog,
        })}
        onCancel={closeDeleteModal}
      />

      <CreateUserModal
        open={createModalVisible}
        creating={creating}
        form={createForm}
        onOk={() => handleCreate({
          createForm,
          message,
          setCreating,
          setUsers,
          setTwoFactorDialog,
          closeCreateModal,
          currentUser,
          openTwoFactorDialog,
        })}
        onCancel={closeCreateModal}
      />

      <DangerousActionTwoFactorModal
        open={Boolean(twoFactorDialog)}
        title={twoFactorDialog?.title ?? '二步验证'}
        description={twoFactorDialog?.description ?? ''}
        loading={saving || deleting || creating || resettingPassword}
        onCancel={() => setTwoFactorDialog(null)}
        onConfirm={async (code) => {
          if (!twoFactorDialog) return
          await twoFactorDialog.onConfirm(code)
        }}
      />
    </Flex>
  )
}
