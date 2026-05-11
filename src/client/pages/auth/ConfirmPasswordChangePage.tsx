import {
  Alert,
  App,
  Button,
  Card,
  Flex,
  Form,
  Input,
  Space,
  Typography,
} from 'antd'
import { LockOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { resolveApiErrorMessage } from '../../lib/error'

export default function ConfirmPasswordChangePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { confirmPasswordChange, isAuthenticated } = useAuth()
  const { message } = App.useApp()

  const [form] = Form.useForm<{ newPassword: string; confirmPassword: string }>()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const tokenValid = useMemo(() => Boolean(token && token.length === 64), [token])

  const handleSubmit = async (values: { newPassword: string; confirmPassword: string }) => {
    if (!token) {
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await confirmPasswordChange({
        token,
        new_password: values.newPassword,
      })
      message.success('密码已更新')
      navigate(isAuthenticated ? '/profile' : '/login', { replace: true })
    } catch (err) {
      const text = resolveApiErrorMessage(err, '密码修改失败，请稍后重试。')
      setError(text)
      message.error(text)
    } finally {
      setSubmitting(false)
    }
  }

  if (!tokenValid) {
    return (
      <Flex align="center" justify="center" style={{ minHeight: '100vh', padding: '48px 16px' }}>
        <Card bordered={false} className="theme-card-shadow" style={{ width: '100%', maxWidth: 420 }}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Typography.Title level={4} style={{ marginBottom: 0 }}>
              确认链接无效
            </Typography.Title>
            <Typography.Text type="secondary">
              请确认链接是否完整，或重新从个人中心发送密码修改确认邮件。
            </Typography.Text>
            <Link to={isAuthenticated ? '/profile' : '/login'} className="theme-link">
              返回
            </Link>
          </Space>
        </Card>
      </Flex>
    )
  }

  return (
    <Flex align="center" justify="center" style={{ minHeight: '100vh', padding: '48px 16px' }}>
      <Card bordered={false} className="theme-card-shadow" style={{ width: '100%', maxWidth: 420 }}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 8 }}>
              确认修改密码
            </Typography.Title>
            <Typography.Text type="secondary">
              该链接验证通过后，将直接把您的登录密码更新为新密码。
            </Typography.Text>
          </div>
          {error && <Alert type="error" showIcon message={error} />}
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            requiredMark={false}
          >
            <Form.Item
              label="新密码"
              name="newPassword"
              rules={[
                { required: true, message: '请输入新密码' },
                { min: 8, message: '密码至少 8 个字符' },
              ]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请输入新密码"
                autoComplete="new-password"
              />
            </Form.Item>
            <Form.Item
              label="确认新密码"
              name="confirmPassword"
              dependencies={['newPassword']}
              rules={[
                { required: true, message: '请再次输入新密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('newPassword') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'))
                  },
                }),
              ]}
            >
              <Input.Password
                size="large"
                prefix={<SafetyCertificateOutlined />}
                placeholder="请再次输入新密码"
                autoComplete="new-password"
              />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" size="large" loading={submitting} block>
                确认修改
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </Flex>
  )
}
