import {
  Alert,
  App,
  Button,
  Card,
  Checkbox,
  Flex,
  Form,
  Input,
  Modal,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { KeyOutlined, ReloadOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { TableColumnsType } from 'antd'
import { listScopes, listUsers, updateUserScopes } from '../../lib/admin'
import type { AdminScope, AdminUser } from '../../lib/types'
import { resolveApiErrorMessage } from '../../lib/error'
import { useAuth } from '../../hooks/useAuth'
import DangerousActionTwoFactorModal from '../../components/auth/DangerousActionTwoFactorModal'

interface ScopeFormValues {
  scopes: string[]
}

function resolveScopeCategoryColor(category: AdminScope['category']): string {
  if (category === 'dangerous') {
    return 'red'
  }
  if (category === 'sensitive') {
    return 'volcano'
  }
  return 'blue'
}

export default function PermissionManagementPage() {
  const { message } = App.useApp()
  const { user: currentUser } = useAuth()
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const [users, setUsers] = useState<AdminUser[]>([])
  const [scopes, setScopes] = useState<AdminScope[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [keyword, setKeyword] = useState('')
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [saving, setSaving] = useState(false)
  const [twoFactorPromptOpen, setTwoFactorPromptOpen] = useState(false)
  const [form] = Form.useForm<ScopeFormValues>()

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [userData, scopeData] = await Promise.all([listUsers(), listScopes()])
      setUsers(userData)
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

  const scopeMap = useMemo(() => {
    return new Map(scopes.map((item) => [item.scope, item]))
  }, [scopes])

  const filteredUsers = useMemo(() => {
    const trimmed = keyword.trim().toLowerCase()
    if (!trimmed) {
      return users
    }
    return users.filter((user) =>
      [
        user.username,
        user.email,
        user.name ?? '',
        ...user.effective_scopes.flatMap((scope) => {
          const scopeMeta = scopeMap.get(scope)
          return [scope, scopeMeta?.title ?? '', scopeMeta?.description ?? '']
        }),
      ]
        .join(' ')
        .toLowerCase()
        .includes(trimmed),
    )
  }, [keyword, scopeMap, users])

  const openEditModal = useCallback(
    (user: AdminUser) => {
      setEditingUser(user)
      form.setFieldsValue({ scopes: user.effective_scopes })
    },
    [form],
  )

  const closeEditModal = useCallback(() => {
    setEditingUser(null)
    form.resetFields()
  }, [form])

  const handleSave = useCallback(async () => {
    if (!editingUser) {
      return
    }

    try {
      const values = await form.validateFields()
      const normalizedScopes = [...values.scopes].sort()
      const existingScopes = [...editingUser.effective_scopes].sort()
      if (normalizedScopes.join(' ') === existingScopes.join(' ')) {
        message.info('没有需要保存的改动')
        closeEditModal()
        return
      }

      const performSave = async (twoFactorCode?: string) => {
        setSaving(true)
        try {
          const updated = await updateUserScopes(
            editingUser.id,
            { scopes: values.scopes },
            twoFactorCode,
          )
          setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
          message.success(`已更新 ${updated.username} 的权限范围`)
          closeEditModal()
          setTwoFactorPromptOpen(false)
        } finally {
          setSaving(false)
        }
      }

      if (currentUser?.two_factor_enabled) {
        setTwoFactorPromptOpen(true)
        return
      }

      await performSave()
    } catch (err) {
      if (typeof err === 'object' && err && 'errorFields' in err) {
        return
      }
      message.error(resolveApiErrorMessage(err, '请求失败，请稍后再试。'))
    }
  }, [closeEditModal, currentUser?.two_factor_enabled, editingUser, form, message])

  const columns: TableColumnsType<AdminUser> = useMemo(
    () => [
      {
        title: '用户',
        key: 'user',
        render: (_, record) => (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{record.username}</Typography.Text>
            <Typography.Text type="secondary">{record.email}</Typography.Text>
          </Space>
        ),
      },
      {
        title: '角色',
        dataIndex: 'role',
        key: 'role',
        render: (value: AdminUser['role']) => (
          <Tag color={value === 'admin' ? 'geekblue' : 'default'}>
            {value === 'admin' ? '管理员' : '普通用户'}
          </Tag>
        ),
      },
      {
        title: '当前范围',
        key: 'effective_scopes',
        render: (_, record) => (
          <Flex gap={8} wrap="wrap">
            {record.effective_scopes.map((scope) => {
              const scopeMeta = scopeMap.get(scope)
              return (
                <Tag
                  key={`${record.id}-${scope}`}
                  color={scopeMeta ? resolveScopeCategoryColor(scopeMeta.category) : 'default'}
                >
                  {scopeMeta?.title ?? scope}
                </Tag>
              )
            })}
          </Flex>
        ),
      },
      {
        title: '操作',
        key: 'actions',
        render: (_, record) => (
          <Button
            size="small"
            onClick={() => openEditModal(record)}
            disabled={record.id === currentUser?.id || saving}
          >
            配置权限
          </Button>
        ),
      },
    ],
    [currentUser?.id, openEditModal, saving, scopeMap],
  )

  const editingOptions = useMemo(() => {
    if (!editingUser) {
      return []
    }
    return editingUser.available_scopes.map((scope) => {
      const scopeMeta = scopeMap.get(scope)
      return {
        value: scope,
        label: (
          <Space size={8} wrap>
            <Typography.Text code>{scope}</Typography.Text>
            {scopeMeta && (
              <>
                <Tag color={resolveScopeCategoryColor(scopeMeta.category)}>
                  {scopeMeta.category === 'dangerous'
                    ? '危险'
                    : scopeMeta.category === 'sensitive'
                      ? '敏感'
                      : '普通'}
                </Tag>
                <Typography.Text strong>{scopeMeta.title}</Typography.Text>
                <Typography.Text type="secondary">{scopeMeta.description}</Typography.Text>
              </>
            )}
          </Space>
        ),
      }
    })
  }, [editingUser, scopeMap])

  return (
    <Flex vertical gap={24}>
      <Card>
        <Flex align={isMobile ? 'stretch' : 'center'} justify="space-between" wrap="wrap" gap={16} vertical={isMobile}>
          <Space>
            <KeyOutlined style={{ fontSize: 20 }} />
            <Typography.Title level={4} style={{ margin: 0 }}>
              权限管理
            </Typography.Title>
          </Space>
          <Flex wrap="wrap" gap={8} style={{ width: isMobile ? '100%' : 'auto' }}>
            <Input
              placeholder="搜索用户 / 权限"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              allowClear
              style={{ minWidth: isMobile ? '100%' : 240, flex: isMobile ? 1 : 'auto' }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
              {isMobile ? '' : '刷新'}
            </Button>
          </Flex>
        </Flex>
        <Typography.Paragraph type="secondary" className="mt-4">
          在这里管理每个用户当前角色范围内实际生效的权限。修改后会立即使该用户现有会话失效。
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
          locale={{ emptyText: '暂无用户权限数据' }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      <Modal
        title={editingUser ? `配置权限：${editingUser.username}` : '配置权限'}
        open={Boolean(editingUser)}
        onCancel={closeEditModal}
        onOk={handleSave}
        okText="保存"
        confirmLoading={saving}
        destroyOnClose
        width={isMobile ? '95%' : 720}
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Alert
            type="warning"
            showIcon
            message="权限范围必须属于当前角色允许的权限子集"
            description="如果之后修改用户角色，系统会自动将权限范围重置为新角色的默认权限集合。"
          />
          <Form form={form} layout="vertical" requiredMark={false}>
            <Form.Item label="角色">
              <Typography.Text>{editingUser?.role === 'admin' ? '管理员' : '普通用户'}</Typography.Text>
            </Form.Item>
            <Form.Item
              label="生效权限"
              name="scopes"
            >
              <Checkbox.Group options={editingOptions} style={{ width: '100%' }} />
            </Form.Item>
          </Form>
        </Space>
      </Modal>

      <DangerousActionTwoFactorModal
        open={twoFactorPromptOpen}
        title="二步验证后更新用户权限范围"
        description="修改用户权限范围属于危险操作，请先完成二步验证。"
        loading={saving}
        onCancel={() => setTwoFactorPromptOpen(false)}
        onConfirm={async (code) => {
          if (!editingUser) {
            return
          }
          try {
            const values = await form.validateFields()
            setSaving(true)
            const updated = await updateUserScopes(editingUser.id, { scopes: values.scopes }, code)
            setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
            message.success(`已更新 ${updated.username} 的权限范围`)
            closeEditModal()
            setTwoFactorPromptOpen(false)
          } catch (err) {
            message.error(resolveApiErrorMessage(err, '请求失败，请稍后再试。'))
          } finally {
            setSaving(false)
          }
        }}
      />
    </Flex>
  )
}
