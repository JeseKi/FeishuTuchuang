import { Form, Input, Modal, Select } from 'antd'
import type { FormInstance } from 'antd'
import { roleOptions, statusOptions } from './utils'

interface CreateUserModalProps {
  open: boolean
  creating: boolean
  form: FormInstance
  onOk: () => void
  onCancel: () => void
}

export default function CreateUserModal({
  open,
  creating,
  form,
  onOk,
  onCancel,
}: CreateUserModalProps) {
  return (
    <Modal
      title="创建用户"
      open={open}
      onCancel={onCancel}
      onOk={onOk}
      okText="创建"
      confirmLoading={creating}
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
            { max: 50, message: '用户名不能超过 50 个字符' },
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
        <Form.Item
          label="密码"
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 8, message: '密码至少 8 位' },
          ]}
        >
          <Input.Password placeholder="请输入密码" />
        </Form.Item>
        <Form.Item
          label="确认密码"
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: '请再次输入密码' },
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
          <Input.Password placeholder="请再次输入密码" />
        </Form.Item>
        <Form.Item label="角色" name="role">
          <Select options={roleOptions} />
        </Form.Item>
        <Form.Item label="状态" name="status">
          <Select options={statusOptions} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
