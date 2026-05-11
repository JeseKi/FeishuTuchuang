import { App, Alert, Button, Card, Flex, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd'
import { LockOutlined, ReloadOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { TableColumnsType } from 'antd'
import { listScopes, updateScope } from '../../lib/admin'
import type { AdminScope, ScopeCategory } from '../../lib/types'
import { resolveApiErrorMessage } from '../../lib/error'
import { useAuth } from '../../hooks/useAuth'
import DangerousActionTwoFactorModal from '../../components/auth/DangerousActionTwoFactorModal'

interface ScopeFormValues {
  category: ScopeCategory
}

const categoryOptions = [
  { value: 'normal', label: '普通' },
  { value: 'sensitive', label: '敏感' },
  { value: 'dangerous', label: '危险' },
]

export default function ScopeManagementPage() {
  const { message } = App.useApp()
  const { user } = useAuth()
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const [scopes, setScopes] = useState<AdminScope[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [keyword, setKeyword] = useState('')
  const [editingScope, setEditingScope] = useState<AdminScope | null>(null)
  const [saving, setSaving] = useState(false)
  const [twoFactorPromptOpen, setTwoFactorPromptOpen] = useState(false)
  const [form] = Form.useForm<ScopeFormValues>()

  const loadScopes = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listScopes()
      setScopes(data)
    } catch (err) {
      const text = resolveApiErrorMessage(err, '请求失败，请稍后再试。')
      setError(text)
      message.error(text)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadScopes()
  }, [loadScopes])

  const filteredScopes = useMemo(() => {
    const trimmed = keyword.trim().toLowerCase()
    if (!trimmed) {
      return scopes
    }
    return scopes.filter((item) =>
      [item.scope, item.title, item.description].join(' ').toLowerCase().includes(trimmed),
    )
  }, [keyword, scopes])

  const openEditModal = useCallback(
    (scope: AdminScope) => {
      setEditingScope(scope)
      form.setFieldsValue({ category: scope.category })
    },
    [form],
  )

  const closeEditModal = useCallback(() => {
    setEditingScope(null)
    form.resetFields()
  }, [form])

  const handleSave = useCallback(async () => {
    if (!editingScope) {
      return
    }

    try {
      const values = await form.validateFields()
      if (values.category === editingScope.category) {
        message.info('没有需要保存的改动')
        closeEditModal()
        return
      }

      const performSave = async (twoFactorCode?: string) => {
        setSaving(true)
        try {
          const updated = await updateScope(editingScope.scope, { category: values.category }, twoFactorCode)
          setScopes((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
          message.success(`已更新 ${updated.scope} 的分类`)
          closeEditModal()
          setTwoFactorPromptOpen(false)
        } finally {
          setSaving(false)
        }
      }

      if (user?.two_factor_enabled) {
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
  }, [closeEditModal, editingScope, form, message, user?.two_factor_enabled])

  const columns: TableColumnsType<AdminScope> = useMemo(
    () => [
      {
        title: '权限',
        key: 'permission',
        render: (_, record) => (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{record.title}</Typography.Text>
            <Typography.Text type="secondary">{record.description}</Typography.Text>
          </Space>
        ),
      },
      {
        title: '技术标识',
        dataIndex: 'scope',
        key: 'scope',
        render: (value: string) => <Typography.Text code>{value}</Typography.Text>,
      },
      {
        title: '分类',
        dataIndex: 'category',
        key: 'category',
        render: (value: ScopeCategory) => (
          <Tag color={value === 'dangerous' ? 'red' : value === 'sensitive' ? 'volcano' : 'blue'}>
            {value === 'dangerous' ? '危险' : value === 'sensitive' ? '敏感' : '普通'}
          </Tag>
        ),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        key: 'updated_at',
        render: (value: string) => new Date(value).toLocaleString(),
      },
      {
        title: '操作',
        key: 'actions',
        render: (_, record) => (
          <Button size="small" onClick={() => openEditModal(record)} disabled={saving}>
            修改分类
          </Button>
        ),
      },
    ],
    [openEditModal, saving],
  )

  return (
    <Flex vertical gap={24}>
      <Card>
        <Flex align={isMobile ? 'stretch' : 'center'} justify="space-between" wrap="wrap" gap={16} vertical={isMobile}>
          <Space>
            <LockOutlined style={{ fontSize: 20 }} />
            <Typography.Title level={4} style={{ margin: 0 }}>
              Scope 管理
            </Typography.Title>
          </Space>
          <Flex wrap="wrap" gap={8} style={{ width: isMobile ? '100%' : 'auto' }}>
            <Input
              placeholder="搜索权限 / scope / 说明"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              allowClear
              style={{ minWidth: isMobile ? '100%' : 240, flex: isMobile ? 1 : 'auto' }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadScopes} loading={loading}>
              {isMobile ? '' : '刷新'}
            </Button>
          </Flex>
        </Flex>
        <Typography.Paragraph type="secondary" className="mt-4">
          这里维护系统内置权限的分类。普通用于常规授权，敏感用于重要数据操作，危险用于高风险或破坏性操作。
        </Typography.Paragraph>
      </Card>

      {error && <Alert type="error" showIcon message={error} />}

      <Card bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={filteredScopes}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无 scope 数据' }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      <Modal
        title={editingScope ? `修改分类：${editingScope.title}` : '修改分类'}
        open={Boolean(editingScope)}
        onCancel={closeEditModal}
        onOk={handleSave}
        okText="保存"
        confirmLoading={saving}
        destroyOnClose
        width={isMobile ? '95%' : 520}
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Alert
            type="warning"
            showIcon
            message="危险 scope 应只用于高风险能力"
            description="例如密码修改、管理员写操作或其他可能造成不可逆影响的行为。"
          />
          <Form form={form} layout="vertical" requiredMark={false}>
            <Form.Item label="权限">
              <Space direction="vertical" size={0}>
                <Typography.Text strong>{editingScope?.title}</Typography.Text>
                <Typography.Text type="secondary">{editingScope?.description ?? '-'}</Typography.Text>
              </Space>
            </Form.Item>
            <Form.Item label="技术标识">
              <Typography.Text code>{editingScope?.scope}</Typography.Text>
            </Form.Item>
            <Form.Item
              label="分类"
              name="category"
              rules={[{ required: true, message: '请选择分类' }]}
            >
              <Select options={categoryOptions} />
            </Form.Item>
          </Form>
        </Space>
      </Modal>

      <DangerousActionTwoFactorModal
        open={twoFactorPromptOpen}
        title="二步验证后修改权限分类"
        description="修改权限分类会影响危险操作的鉴权要求，请先完成二步验证。"
        loading={saving}
        onCancel={() => setTwoFactorPromptOpen(false)}
        onConfirm={async (code) => {
          if (!editingScope) {
            return
          }
          try {
            const values = await form.validateFields()
            setSaving(true)
            const updated = await updateScope(editingScope.scope, { category: values.category }, code)
            setScopes((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
            message.success(`已更新 ${updated.scope} 的分类`)
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
