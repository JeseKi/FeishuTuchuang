import { Alert, App, Button, Card, Flex, Form, Input, Space, Table, Typography } from 'antd'
import { ApiOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { listScopes } from '../../../lib/admin'
import {
  createOAuthClient,
  deleteOAuthClient,
  listOAuthClients,
  resetOAuthClientSecret,
  updateOAuthClient,
} from '../../../lib/oauthProvider'
import type { AdminScope, OAuthClient, OAuthClientWithSecret } from '../../../lib/types'
import { resolveApiErrorMessage } from '../../../lib/error'
import { useAuth } from '../../../hooks/useAuth'
import DangerousActionTwoFactorModal from '../../../components/auth/DangerousActionTwoFactorModal'
import ClientFormModal from './ClientFormModal'
import SecretModal from './SecretModal'
import { useColumns } from './columns'
import type { ClientFormValues, PendingTwoFactorAction } from './types'
import { buildFormValues, parseRedirectUris } from './utils'

export default function OAuthClientManagementPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const [isMobile, setIsMobile] = useState(false)
  const [clients, setClients] = useState<OAuthClient[]>([])
  const [scopes, setScopes] = useState<AdminScope[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [keyword, setKeyword] = useState('')
  const [editingClient, setEditingClient] = useState<OAuthClient | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [secretResult, setSecretResult] = useState<OAuthClientWithSecret | null>(null)
  const [pendingTwoFactorAction, setPendingTwoFactorAction] = useState<PendingTwoFactorAction | null>(null)
  const [form] = Form.useForm<ClientFormValues>()

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [clientData, scopeData] = await Promise.all([listOAuthClients(), listScopes()])
      setClients(clientData)
      setScopes(scopeData)
    } catch (err) {
      const text = resolveApiErrorMessage(err, '请求失败，请稍后再试。')
      setError(text)
      message.error(text)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const filteredClients = useMemo(() => {
    const trimmed = keyword.trim().toLowerCase()
    if (!trimmed) {
      return clients
    }
    return clients.filter((client) =>
      [client.name, client.client_id, ...client.redirect_uris, ...client.allowed_scopes]
        .join(' ')
        .toLowerCase()
        .includes(trimmed),
    )
  }, [clients, keyword])

  const openCreateModal = useCallback(() => {
    setEditingClient(null)
    form.setFieldsValue(buildFormValues())
    setFormOpen(true)
  }, [form])

  const openEditModal = useCallback(
    (client: OAuthClient) => {
      setEditingClient(client)
      form.setFieldsValue(buildFormValues(client))
      setFormOpen(true)
    },
    [form],
  )

  const closeFormModal = useCallback(() => {
    setFormOpen(false)
    setEditingClient(null)
    form.resetFields()
  }, [form])

  const runProtectedAction = useCallback(
    async (action: PendingTwoFactorAction) => {
      if (user?.two_factor_enabled) {
        setPendingTwoFactorAction(action)
        return
      }
      await action.run()
    },
    [user?.two_factor_enabled],
  )

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields()
      const redirectUris = parseRedirectUris(values.redirect_uris_text)
      if (redirectUris.length === 0) {
        form.setFields([{ name: 'redirect_uris_text', errors: ['至少需要一个 redirect_uri'] }])
        return
      }

      const payload = {
        name: values.name.trim(),
        redirect_uris: redirectUris,
        allowed_scopes: values.allowed_scopes ?? [],
        is_active: values.is_active,
        require_pkce: values.require_pkce,
      }

      await runProtectedAction({
        title: editingClient ? '二步验证后更新 OAuth Client' : '二步验证后创建 OAuth Client',
        description: 'OAuth Client 配置会影响第三方应用授权入口，请先完成二步验证。',
        run: async (code?: string) => {
          setSaving(true)
          try {
            if (editingClient) {
              const updated = await updateOAuthClient(editingClient.client_id, payload, code)
              setClients((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
              message.success(`已更新 ${updated.name}`)
            } else {
              const created = await createOAuthClient(payload, code)
              setClients((prev) => [created, ...prev])
              setSecretResult(created)
              message.success(`已创建 ${created.name}`)
            }
            closeFormModal()
            setPendingTwoFactorAction(null)
          } finally {
            setSaving(false)
          }
        },
      })
    } catch (err) {
      if (typeof err === 'object' && err && 'errorFields' in err) {
        return
      }
      message.error(resolveApiErrorMessage(err, '请求失败，请稍后再试。'))
    }
  }, [closeFormModal, editingClient, form, message, runProtectedAction])

  const handleResetSecret = useCallback(
    async (client: OAuthClient) => {
      if (!window.confirm(`确定要重置 ${client.name} 的 client secret 吗？`)) {
        return
      }
      try {
        await runProtectedAction({
          title: '二步验证后重置 Client Secret',
          description: '重置后旧 secret 会立即失效，请先完成二步验证。',
          run: async (code?: string) => {
            setSaving(true)
            try {
              const updated = await resetOAuthClientSecret(client.client_id, code)
              setClients((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
              setSecretResult(updated)
              message.success(`已重置 ${updated.name} 的 secret`)
              setPendingTwoFactorAction(null)
            } finally {
              setSaving(false)
            }
          },
        })
      } catch (err) {
        message.error(resolveApiErrorMessage(err, '请求失败，请稍后再试。'))
      }
    },
    [message, runProtectedAction],
  )

  const handleDelete = useCallback(
    async (client: OAuthClient) => {
      if (!window.confirm(`确定要删除 ${client.name} 吗？`)) {
        return
      }
      try {
        await runProtectedAction({
          title: '二步验证后删除 OAuth Client',
          description: '删除后该第三方应用将无法继续完成 OAuth 授权，请先完成二步验证。',
          run: async (code?: string) => {
            setSaving(true)
            try {
              await deleteOAuthClient(client.client_id, code)
              setClients((prev) => prev.filter((item) => item.id !== client.id))
              message.success(`已删除 ${client.name}`)
              setPendingTwoFactorAction(null)
            } finally {
              setSaving(false)
            }
          },
        })
      } catch (err) {
        message.error(resolveApiErrorMessage(err, '请求失败，请稍后再试。'))
      }
    },
    [message, runProtectedAction],
  )

  const columns = useColumns({
    saving,
    onEdit: openEditModal,
    onResetSecret: (client) => void handleResetSecret(client),
    onDelete: (client) => void handleDelete(client),
  })

  return (
    <Flex vertical gap={24}>
      <Card>
        <Flex align={isMobile ? 'stretch' : 'center'} justify="space-between" wrap="wrap" gap={16} vertical={isMobile}>
          <Space>
            <ApiOutlined style={{ fontSize: 20 }} />
            <Typography.Title level={4} style={{ margin: 0 }}>OAuth Client 管理</Typography.Title>
          </Space>
          <Flex wrap="wrap" gap={8} style={{ width: isMobile ? '100%' : 'auto' }}>
            <Input
              placeholder="搜索应用 / client_id / redirect_uri"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              allowClear
              style={{ minWidth: isMobile ? '100%' : 260, flex: isMobile ? 1 : 'auto' }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
              {isMobile ? '' : '刷新'}
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
              {isMobile ? '' : '创建 Client'}
            </Button>
          </Flex>
        </Flex>
        <Typography.Paragraph type="secondary" className="mt-4">
          在这里管理可接入本系统 OAuth Provider 的第三方应用。
        </Typography.Paragraph>
      </Card>

      {error && <Alert type="error" showIcon message={error} />}

      <Card bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={filteredClients}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无 OAuth Client' }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      <ClientFormModal
        open={formOpen}
        editingClient={editingClient}
        saving={saving}
        isMobile={isMobile}
        scopes={scopes}
        form={form}
        onOk={() => void handleSubmit()}
        onCancel={closeFormModal}
      />

      <SecretModal secretResult={secretResult} isMobile={isMobile} onClose={() => setSecretResult(null)} />

      <DangerousActionTwoFactorModal
        open={Boolean(pendingTwoFactorAction)}
        title={pendingTwoFactorAction?.title ?? '二步验证'}
        description={pendingTwoFactorAction?.description ?? ''}
        loading={saving}
        onCancel={() => setPendingTwoFactorAction(null)}
        onConfirm={async (code) => {
          if (!pendingTwoFactorAction) {
            return
          }
          try {
            await pendingTwoFactorAction.run(code)
          } catch (err) {
            message.error(resolveApiErrorMessage(err, '请求失败，请稍后再试。'))
          }
        }}
      />
    </Flex>
  )
}
