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
import {
  MailOutlined,
  SafetyCertificateOutlined,
  SendOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { resolveApiErrorMessage } from '../../lib/error'

export default function ProfilePage() {
  const { user, update, sendEmailChangeCode, confirmEmailChange } = useAuth()
  const { message } = App.useApp()

  const [profileForm] = Form.useForm<{ username: string; name?: string }>()
  const [emailForm] = Form.useForm<{ email: string; code: string }>()
  const pendingEmail = Form.useWatch('email', emailForm)

  const [profileSubmitting, setProfileSubmitting] = useState(false)
  const [emailSending, setEmailSending] = useState(false)
  const [emailSubmitting, setEmailSubmitting] = useState(false)
  const [emailCountdown, setEmailCountdown] = useState(0)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)

  useEffect(() => {
    profileForm.setFieldsValue({
      username: user?.username ?? '',
      name: user?.name ?? undefined,
    })
  }, [profileForm, user?.name, user?.username])

  useEffect(() => {
    if (emailCountdown <= 0) {
      return
    }

    const timer = window.setInterval(() => {
      setEmailCountdown((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)

    return () => window.clearInterval(timer)
  }, [emailCountdown])

  const handleProfileSubmit = async (values: { username: string; name?: string }) => {
    setProfileSubmitting(true)
    setProfileError(null)
    try {
      const payload = {
        username: values.username.trim(),
        name: values.name?.trim() ? values.name.trim() : null,
      }
      await update(payload)
      message.success('个人资料已更新')
    } catch (error) {
      const text = resolveApiErrorMessage(error, '操作失败，请稍后重试。')
      setProfileError(text)
      message.error(text)
    } finally {
      setProfileSubmitting(false)
    }
  }

  const handleSendEmailCode = async () => {
    const email = emailForm.getFieldValue('email') as string | undefined
    if (!email || emailSending || emailCountdown > 0) {
      return
    }

    setEmailSending(true)
    setEmailError(null)
    try {
      await sendEmailChangeCode({ email })
      setEmailCountdown(60)
      message.success('验证码已发送到新邮箱')
    } catch (error) {
      const text = resolveApiErrorMessage(error, '验证码发送失败，请稍后重试。')
      setEmailError(text)
      message.error(text)
    } finally {
      setEmailSending(false)
    }
  }

  const handleEmailSubmit = async (values: { email: string; code: string }) => {
    setEmailSubmitting(true)
    setEmailError(null)
    try {
      await confirmEmailChange({
        email: values.email.trim(),
        code: values.code.trim(),
      })
      emailForm.resetFields()
      setEmailCountdown(0)
      message.success('邮箱已更新')
    } catch (error) {
      const text = resolveApiErrorMessage(error, '邮箱修改失败，请稍后重试。')
      setEmailError(text)
      message.error(text)
    } finally {
      setEmailSubmitting(false)
    }
  }

  return (
    <Space direction="vertical" size={32} style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ marginBottom: 8 }}>
          个人信息
        </Typography.Title>
        <Typography.Text type="secondary">管理您的用户名和邮箱。</Typography.Text>
      </div>

      <Card title="基础资料" bordered={false} style={{ width: '100%' }}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <Flex vertical gap={4}>
            <Typography.Text type="secondary">当前登录邮箱</Typography.Text>
            <Typography.Text strong>{user?.email ?? '-'}</Typography.Text>
          </Flex>
          {profileError && <Alert type="error" showIcon message={profileError} />}
          <Form
            form={profileForm}
            layout="vertical"
            onFinish={handleProfileSubmit}
            requiredMark={false}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少 3 个字符' },
                { max: 50, message: '用户名不能超过 50 个字符' },
              ]}
              style={{ marginBottom: 20 }}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                allowClear
                size="large"
              />
            </Form.Item>
            <Form.Item
              label="昵称"
              name="name"
              rules={[{ max: 100, message: '昵称不能超过 100 个字符' }]}
              style={{ marginBottom: 20 }}
            >
              <Input placeholder="可选" allowClear size="large" />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" loading={profileSubmitting} size="large">
                保存基础资料
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>

      <Card title="邮箱改绑" bordered={false} style={{ width: '100%' }}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <Typography.Text type="secondary">
            验证码会发送到目标邮箱，输入验证码后才会完成改绑。
          </Typography.Text>
          {emailError && <Alert type="error" showIcon message={emailError} />}
          <Form
            form={emailForm}
            layout="vertical"
            onFinish={handleEmailSubmit}
            requiredMark={false}
          >
            <Form.Item
              label="新邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入新邮箱' },
                { type: 'email', message: '请输入正确的邮箱格式' },
              ]}
              style={{ marginBottom: 20 }}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="请输入新的邮箱地址"
                allowClear
                size="large"
              />
            </Form.Item>
            <Form.Item label="验证码" style={{ marginBottom: 20 }}>
              <Flex gap={12}>
                <Form.Item
                  name="code"
                  noStyle
                  rules={[
                    { required: true, message: '请输入验证码' },
                    { len: 6, message: '验证码应为 6 位' },
                  ]}
                >
                  <Input
                    size="large"
                    prefix={<SafetyCertificateOutlined />}
                    placeholder="请输入邮箱验证码"
                    maxLength={6}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
                <Button
                  size="large"
                  icon={<SendOutlined />}
                  loading={emailSending}
                  disabled={!pendingEmail || emailCountdown > 0}
                  onClick={() => void handleSendEmailCode()}
                  style={{ width: 150, flex: '0 0 150px' }}
                >
                  {emailCountdown > 0 ? `${emailCountdown}s` : '发送验证码'}
                </Button>
              </Flex>
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" loading={emailSubmitting} size="large">
                确认修改邮箱
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </Space>
  )
}
