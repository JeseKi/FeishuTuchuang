import { Alert, Form, Input, Modal, Space } from 'antd'
import type { FormInstance } from 'antd'
import type { AdminUser } from '../../../lib/types'

interface ResetPasswordModalProps {
  open: boolean
  resettingUser: AdminUser | null
  resettingPassword: boolean
  form: FormInstance
  onOk: () => void
  onCancel: () => void
}

export default function ResetPasswordModal({
  open,
  resettingUser,
  resettingPassword,
  form,
  onOk,
  onCancel,
}: ResetPasswordModalProps) {
  return (
    <Modal
      title={resettingUser ? `重置密码：${resettingUser.username}` : '重置密码'}
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      okText="确认重置"
      okButtonProps={{ danger: true }}
      confirmLoading={resettingPassword}
      destroyOnClose
      width={520}
    >
      <Space
        direction="vertical"
        size={16}
        style={{ width: '100%' }}
      >
        <Alert
          type="warning"
          showIcon
          message="该操作会直接将用户密码修改为你输入的新密码。"
          description="请确认这是管理员主动执行的密码重置，并在下方完成完整确认。"
        />
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            label="新密码"
            name="password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 8, message: '密码至少 8 位' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
          <Form.Item
            label="确认新密码"
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请再次输入新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
          <Form.Item
            label='输入"确认重置"'
            name="confirmationText"
            rules={[
              { required: true, message: '请输入确认文本' },
              {
                validator(_, value) {
                  if (typeof value === 'string' && value.trim() === '确认重置') {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('请输入准确的"确认重置"'))
                },
              },
            ]}
          >
            <Input placeholder="请输入确认重置" />
          </Form.Item>
        </Form>
      </Space>
    </Modal>
  )
}
