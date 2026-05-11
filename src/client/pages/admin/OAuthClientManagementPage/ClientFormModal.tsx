import { Flex, Form, Input, Modal, Select, Switch } from 'antd'
import { useMemo } from 'react'
import type { ClientFormModalProps } from './types'

const { TextArea } = Input

export default function ClientFormModal({
  open,
  editingClient,
  saving,
  isMobile,
  scopes,
  form,
  onOk,
  onCancel,
}: ClientFormModalProps) {
  const scopeOptions = useMemo(
    () =>
      scopes.map((scope) => ({
        value: scope.scope,
        label: `${scope.title} (${scope.scope})`,
      })),
    [scopes],
  )

  return (
    <Modal
      title={editingClient ? `编辑 Client：${editingClient.name}` : '创建 OAuth Client'}
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      okText={editingClient ? '保存' : '创建'}
      confirmLoading={saving}
      destroyOnClose
      width={isMobile ? '95%' : 720}
    >
      <Form form={form} layout="vertical" requiredMark={false}>
        <Form.Item label="应用名称" name="name" rules={[{ required: true, message: '请输入应用名称' }]}>
          <Input placeholder="例如 Demo OAuth App" />
        </Form.Item>
        <Form.Item
          label="Redirect URIs"
          name="redirect_uris_text"
          rules={[{ required: true, message: '请输入 redirect_uri' }]}
        >
          <TextArea rows={4} placeholder="每行一个 redirect_uri" />
        </Form.Item>
        <Form.Item label="允许的 Scopes" name="allowed_scopes">
          <Select mode="multiple" options={scopeOptions} placeholder="选择允许授权的 scope" />
        </Form.Item>
        <Flex gap={24} wrap="wrap">
          <Form.Item label="启用状态" name="is_active" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item label="要求 PKCE" name="require_pkce" valuePropName="checked">
            <Switch checkedChildren="要求" unCheckedChildren="关闭" />
          </Form.Item>
        </Flex>
      </Form>
    </Modal>
  )
}
