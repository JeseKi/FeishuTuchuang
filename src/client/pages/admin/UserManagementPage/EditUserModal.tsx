import { Button, Form, Input, Modal, Select, Space, Typography } from 'antd'
import type { FormInstance } from 'antd'
import type { AdminUser } from '../../../lib/types'
import { roleOptions, statusOptions } from './utils'

interface EditUserModalProps {
  open: boolean
  editingUser: AdminUser | null
  saving: boolean
  currentUserId?: number
  form: FormInstance
  onOk: () => void
  onCancel: () => void
  onResetPassword: (user: AdminUser) => void
}

export default function EditUserModal({
  open,
  editingUser,
  saving,
  currentUserId,
  form,
  onOk,
  onCancel,
  onResetPassword,
}: EditUserModalProps) {
  return (
    <Modal
      title={editingUser ? `编辑用户：${editingUser.username}` : '编辑用户'}
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      okText="保存"
      confirmLoading={saving}
      destroyOnClose
      width={520}
    >
      <Form
        form={form}
        layout="vertical"
        requiredMark={false}
      >
        <Form.Item
          label="用户名"
          name="username"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少需要 3 个字符' },
          ]}
        >
          <Input placeholder="请输入用户名" />
        </Form.Item>
        <Form.Item
          label="邮箱"
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效邮箱' },
          ]}
        >
          <Input placeholder="请输入邮箱" />
        </Form.Item>
        <Form.Item label="姓名" name="name">
          <Input placeholder="可选" />
        </Form.Item>
        <Form.Item label="角色" name="role">
          <Select
            options={roleOptions}
            disabled={editingUser?.id === currentUserId}
          />
        </Form.Item>
        <Form.Item label="状态" name="status">
          <Select
            options={statusOptions}
            disabled={editingUser?.id === currentUserId}
          />
        </Form.Item>
        <Form.Item label="密码管理">
          <Space
            direction="vertical"
            size={8}
            style={{ width: '100%' }}
          >
            <Button
              danger
              onClick={() => editingUser && onResetPassword(editingUser)}
            >
              重置密码
            </Button>
            <Typography.Text type="secondary">
              重置密码需要在单独弹窗内输入两次新密码，并输入"确认重置"后才会提交。
            </Typography.Text>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}
