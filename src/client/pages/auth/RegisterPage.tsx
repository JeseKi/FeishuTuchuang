import {
  Alert,
  App,
  Button,
  Card,
  Flex,
  Form,
  Input,
  Space,
  Spin,
  Typography,
} from 'antd'
import {
  LockOutlined,
  MailOutlined,
  SendOutlined,
  UserAddOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import TurnstileWidget from '../../components/auth/TurnstileWidget'
import { useAuth } from '../../hooks/useAuth'
import { useRuntimeConfig } from '../../hooks/useRuntimeConfig'
import { resolveApiErrorMessage } from '../../lib/error'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { registerWithCode, sendVerificationCode, loading, isAuthenticated } = useAuth()
  const { turnstile } = useRuntimeConfig()
  const { message } = App.useApp()
  const turnstileSiteKey = turnstile.siteKey
  const turnstileEnabled = turnstile.enabled

  const [form] = Form.useForm<{ username: string; email: string; password: string; confirmPassword: string; code: string }>()
  const [submitting, setSubmitting] = useState(false)
  const [sendingCode, setSendingCode] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [codeCountdown, setCodeCountdown] = useState(0)
  const [registerTurnstileToken, setRegisterTurnstileToken] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

  const handleSendCode = async (email: string) => {
    if (turnstileEnabled && !registerTurnstileToken) {
      const noTokenError = '请先完成机器人校验'
      setError(noTokenError)
      message.error(noTokenError)
      return
    }
    setSendingCode(true)
    setError(null)
    try {
      await sendVerificationCode({ email, turnstile_token: registerTurnstileToken ?? undefined })
      setCodeCountdown(60)
      message.success('验证码已发送，请查看您的邮箱')
    } catch (err) {
      const text = resolveApiErrorMessage(err, '注册失败，请稍后再试。')
      setError(text)
      message.error(text)
    } finally {
      setSendingCode(false)
    }
  }

  useEffect(() => {
    if (codeCountdown <= 0) {
      return
    }

    const timer = window.setInterval(() => {
      setCodeCountdown((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)

    return () => window.clearInterval(timer)
  }, [codeCountdown])

  const handleSubmit = async (values: { username: string; email: string; password: string; confirmPassword: string; code: string }) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { confirmPassword: _confirmPassword, ...payload } = values
    if (turnstileEnabled && !registerTurnstileToken) {
      const noTokenError = '请先完成机器人校验'
      setError(noTokenError)
      message.error(noTokenError)
      return
    }
    setSubmitting(true)
    setError(null)
    setSuccessMessage(null)
    try {
      await registerWithCode({ ...payload, turnstile_token: registerTurnstileToken ?? undefined })
      setSuccessMessage('注册成功，请使用新账号登录。')
      message.success('注册成功')
      navigate('/login', { state: { registerSuccess: true } })
      form.resetFields()
      setCodeCountdown(0)
    } catch (err) {
      const text = resolveApiErrorMessage(err, '注册失败，请稍后再试。')
      setError(text)
      message.error(text)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <Flex
        align="center"
        justify="center"
        style={{ minHeight: '100vh' }}
      >
        <Spin tip="正在加载，请稍候" size="large" />
      </Flex>
    )
  }

  return (
    <Flex
      align="center"
      justify="center"
      style={{ minHeight: '100vh', padding: '48px 16px' }}
    >
      <Card
        bordered={false}
        className="theme-card-shadow"
        style={{ width: '100%', maxWidth: 420 }}
      >
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 8 }}>
              创建新账号
            </Typography.Title>
            <Typography.Text type="secondary">
              需要完成邮箱验证码验证后才能注册。
            </Typography.Text>
          </div>
          {error && <Alert type="error" showIcon message={error} />}
          {successMessage && <Alert type="success" showIcon message={successMessage} />}
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            requiredMark={false}
            autoComplete="on"
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少 3 个字符' },
              ]}
            >
              <Input
                size="large"
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                autoComplete="username"
                allowClear
              />
            </Form.Item>
            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入正确的邮箱格式' },
              ]}
            >
              <Input
                size="large"
                prefix={<MailOutlined />}
                placeholder="请输入邮箱地址"
                autoComplete="email"
                allowClear
              />
            </Form.Item>
            <Form.Item label="验证码">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <Form.Item
                    name="code"
                    noStyle
                    rules={[
                      { required: true, message: '请输入验证码' },
                      { len: 6, message: '验证码为6位数字' },
                    ]}
                  >
                    <Input
                      size="large"
                      style={{ width: '100%' }}
                      placeholder="请输入验证码"
                    />
                  </Form.Item>
                </div>
                <Button
                  size="large"
                  icon={<SendOutlined />}
                  onClick={async () => {
                    try {
                      const values = await form.validateFields(['email'])
                      await handleSendCode(values.email)
                    } catch {
                      // 表单会自行展示错误信息
                    }
                  }}
                  loading={sendingCode}
                  disabled={sendingCode || codeCountdown > 0}
                  style={{ width: 112, flex: '0 0 112px' }}
                >
                  {codeCountdown > 0 ? `${codeCountdown}s` : '发送'}
                </Button>
              </div>
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, message: '密码至少 8 个字符' },
              ]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                autoComplete="new-password"
              />
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
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请再次输入密码"
                autoComplete="new-password"
              />
            </Form.Item>
            {turnstileEnabled ? (
              <Form.Item>
                <TurnstileWidget
                  siteKey={turnstileSiteKey}
                  scriptUrl={turnstile.scriptUrl}
                  action="auth_register_with_code"
                  onToken={setRegisterTurnstileToken}
                />
              </Form.Item>
            ) : null}
            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                icon={<UserAddOutlined />}
                loading={submitting}
                block
              >
                注册
              </Button>
            </Form.Item>
          </Form>
          <Flex justify="center" gap={8}>
            <Typography.Text type="secondary">已有账号？</Typography.Text>
            <Link to="/login" className="theme-link">
              返回登录
            </Link>
          </Flex>
        </Space>
      </Card>
    </Flex>
  )
}
