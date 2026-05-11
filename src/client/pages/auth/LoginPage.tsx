import {
  Alert,
  App,
  Button,
  Card,
  Divider,
  Flex,
  Form,
  Input,
  Modal,
  Space,
  Spin,
  Typography,
} from 'antd'
import {
  ArrowLeftOutlined,
  GithubOutlined,
  GoogleOutlined,
  KeyOutlined,
  LockOutlined,
  LoginOutlined,
  MailOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import TurnstileWidget from '../../components/auth/TurnstileWidget'
import { useAuth } from '../../hooks/useAuth'
import { useRuntimeConfig } from '../../hooks/useRuntimeConfig'
import { resolveApiErrorMessage } from '../../lib/error'
import {
  buildOAuthAuthorizeUrl,
  fetchOAuthProviders,
} from '../../lib/auth'
import type { OAuthProviderInfo } from '../../lib/types'

function normalizeRedirectPath(path: string | null | undefined): string | null {
  if (!path || !path.startsWith('/') || path.startsWith('//')) {
    return null
  }
  return path
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { exchangeOAuthTicket, login, verifyTwoFactorLogin, loading, isAuthenticated, sendPasswordResetLink } = useAuth()
  const { turnstile } = useRuntimeConfig()
  const { message } = App.useApp()
  const turnstileSiteKey = turnstile.siteKey
  const turnstileEnabled = turnstile.enabled

  const [form] = Form.useForm<{ username: string; password: string }>()
  const [twoFactorForm] = Form.useForm<{ code: string }>()
  const [resetForm] = Form.useForm<{ email: string }>()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendingChallengeToken, setPendingChallengeToken] = useState<string | null>(null)
  const [useBackupCode, setUseBackupCode] = useState(false)
  const [resetOpen, setResetOpen] = useState(false)
  const [resetSending, setResetSending] = useState(false)
  const [resetError, setResetError] = useState<string | null>(null)
  const [resetCountdown, setResetCountdown] = useState(0)
  const [resetTurnstileToken, setResetTurnstileToken] = useState<string | null>(null)
  const [oauthProviders, setOauthProviders] = useState<OAuthProviderInfo[]>([])
  const [loginTurnstileToken, setLoginTurnstileToken] = useState<string | null>(null)
  const handledOAuthTicketRef = useRef<string | null>(null)
  const handledOAuthErrorRef = useRef<string | null>(null)

  const locationState = location.state as
    | { from?: { pathname?: string; search?: string }; registerSuccess?: boolean }
    | undefined
  const registerSuccess = locationState?.registerSuccess ?? false

  const searchParams = new URLSearchParams(location.search)
  const oauthTicket = searchParams.get('oauth_ticket')
  const oauthError = searchParams.get('oauth_error')
  const oauthRedirectPath = normalizeRedirectPath(searchParams.get('oauth_redirect_path'))
  const locationRedirectPath = locationState?.from?.pathname
    ? `${locationState.from.pathname}${locationState.from.search ?? ''}`
    : undefined
  const redirectPath = oauthRedirectPath ?? locationRedirectPath ?? '/'

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, loading, navigate])

  useEffect(() => {
    let alive = true

    fetchOAuthProviders()
      .then((providers) => {
        if (alive) {
          setOauthProviders(providers)
        }
      })
      .catch((err) => {
        console.error('【登录页面】获取 OAuth 渠道失败', err)
        if (alive) {
          setOauthProviders([])
        }
      })

    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    if (!oauthError || handledOAuthErrorRef.current === oauthError) {
      return
    }
    handledOAuthErrorRef.current = oauthError
    setError(oauthError)
    message.error(oauthError)
    navigate('/login', { replace: true, state: location.state })
  }, [location.state, message, navigate, oauthError])

  useEffect(() => {
    if (!oauthTicket || handledOAuthTicketRef.current === oauthTicket) {
      return
    }
    handledOAuthTicketRef.current = oauthTicket

    const exchange = async () => {
      setSubmitting(true)
      setError(null)
      try {
        const result = await exchangeOAuthTicket({ ticket: oauthTicket })
        if ('requires_2fa' in result) {
          setPendingChallengeToken(result.challenge_token)
          setUseBackupCode(false)
          twoFactorForm.resetFields()
          message.info('OAuth 验证通过，请继续输入双因素验证码。')
          navigate('/login', {
            replace: true,
            state: { from: { pathname: redirectPath } },
          })
          return
        }
        message.success('欢迎回来')
        navigate(redirectPath, { replace: true })
      } catch (err) {
        console.error('【登录页面】OAuth 票据交换失败', err)
        const text = resolveApiErrorMessage(err, 'OAuth 登录失败，请稍后重试。')
        setError(text)
        message.error(text)
        navigate('/login', { replace: true, state: location.state })
      } finally {
        setSubmitting(false)
      }
    }

    void exchange()
  }, [
    exchangeOAuthTicket,
    location.state,
    message,
    navigate,
    oauthTicket,
    redirectPath,
    twoFactorForm,
  ])

  useEffect(() => {
    if (resetCountdown <= 0) {
      return
    }

    const timer = window.setInterval(() => {
      setResetCountdown((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)

    return () => window.clearInterval(timer)
  }, [resetCountdown])

  const handleSubmit = async (values: { username: string; password: string }) => {
    console.log('【登录页面】提交数据', { 登录标识: values.username })
    if (turnstileEnabled && !loginTurnstileToken) {
      const noTokenError = '请先完成机器人校验'
      setError(noTokenError)
      message.error(noTokenError)
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const result = await login({
        ...values,
        turnstile_token: loginTurnstileToken ?? undefined,
      })
      if ('requires_2fa' in result) {
        setPendingChallengeToken(result.challenge_token)
        setUseBackupCode(false)
        twoFactorForm.resetFields()
        message.info('密码验证通过，请继续输入双因素验证码。')
        return
      }
      message.success('欢迎回来')
      navigate(redirectPath, { replace: true })
    } catch (err) {
      console.error('【登录页面】调用登录接口失败', err)
      const text = resolveApiErrorMessage(err, '登录失败，请稍后重试。')
      setError(text)
      message.error(text)
    } finally {
      setSubmitting(false)
    }
  }

  const handleVerifyTwoFactor = async (values: { code: string }) => {
    if (!pendingChallengeToken) {
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await verifyTwoFactorLogin({
        challenge_token: pendingChallengeToken,
        code: values.code.trim(),
      })
      message.success(useBackupCode ? 'backup code 验证通过' : '双因素验证通过')
      navigate(redirectPath, { replace: true })
    } catch (err) {
      const text = resolveApiErrorMessage(err, '双因素验证失败，请稍后重试。')
      setError(text)
      message.error(text)
    } finally {
      setSubmitting(false)
    }
  }

  const handleBackToPassword = () => {
    setPendingChallengeToken(null)
    setUseBackupCode(false)
    setError(null)
    twoFactorForm.resetFields()
  }

  const handleSendResetLink = async (email: string) => {
    if (turnstileEnabled && !resetTurnstileToken) {
      const noTokenError = '请先完成机器人校验'
      setResetError(noTokenError)
      message.error(noTokenError)
      return
    }
    if (resetCountdown > 0 || resetSending) {
      return
    }
    setResetSending(true)
    setResetError(null)
    try {
      await sendPasswordResetLink({
        email,
        turnstile_token: resetTurnstileToken ?? undefined,
      })
      setResetCountdown(60)
      message.success('重置链接已发送，请查看您的邮箱')
    } catch (err) {
      const text = resolveApiErrorMessage(err, '重置链接发送失败，请稍后重试。')
      setResetError(text)
      message.error(text)
    } finally {
      setResetSending(false)
    }
  }

  if (loading) {
    return (
      <Flex
        align="center"
        justify="center"
        style={{ minHeight: '100vh' }}
      >
        <Spin tip="正在验证登录状态" size="large" />
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
              欢迎回来
            </Typography.Title>
            <Typography.Text type="secondary">
              输入用户名或邮箱及密码以访问现代化的前端模板。
            </Typography.Text>
          </div>
          {registerSuccess && <Alert type="success" showIcon message="注册成功，请使用新账号登录。" style={{ marginBottom: 0 }} />}
          {error && <Alert type="error" showIcon message={error} />}
          {pendingChallengeToken ? (
            <Space direction="vertical" size={20} style={{ width: '100%' }}>
              <Alert
                type="info"
                showIcon
                message="密码已验证"
                description={useBackupCode ? '请输入一条尚未使用过的 backup code。' : '请输入身份验证器当前显示的 6 位动态码。'}
              />
              <Form
                form={twoFactorForm}
                layout="vertical"
                onFinish={handleVerifyTwoFactor}
                requiredMark={false}
                autoComplete="off"
              >
                <Form.Item
                  label={useBackupCode ? 'Backup Code' : '验证码'}
                  name="code"
                  rules={[
                    { required: true, message: useBackupCode ? '请输入 backup code' : '请输入验证码' },
                    { min: 6, message: useBackupCode ? 'backup code 长度不正确' : '验证码至少 6 位' },
                  ]}
                >
                  <Input
                    size="large"
                    prefix={useBackupCode ? <KeyOutlined /> : <SafetyCertificateOutlined />}
                    placeholder={useBackupCode ? '例如 ABCD-EFGH' : '请输入 6 位验证码'}
                    maxLength={useBackupCode ? 32 : 6}
                    autoFocus
                    allowClear
                  />
                </Form.Item>
                <Form.Item style={{ marginBottom: 12 }}>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    icon={<SafetyCertificateOutlined />}
                    loading={submitting}
                    block
                  >
                    完成验证
                  </Button>
                </Form.Item>
              </Form>
              <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
                <Button
                  type="link"
                  icon={<ArrowLeftOutlined />}
                  onClick={handleBackToPassword}
                  style={{ paddingInline: 0 }}
                >
                  返回重新输入密码
                </Button>
                <Button
                  type="link"
                  onClick={() => {
                    setUseBackupCode((prev) => !prev)
                    setError(null)
                    twoFactorForm.resetFields()
                  }}
                  style={{ paddingInline: 0 }}
                >
                  {useBackupCode ? '改用身份验证器验证码' : '使用 backup code'}
                </Button>
              </Flex>
            </Space>
          ) : (
            <>
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
                requiredMark={false}
                autoComplete="on"
              >
                <Form.Item
                  label="用户名/邮箱"
                  name="username"
                  rules={[
                    { required: true, message: '请输入用户名或邮箱' },
                    { min: 3, message: '用户名或邮箱至少 3 个字符' },
                  ]}
                >
                  <Input
                    size="large"
                    prefix={<UserOutlined />}
                    placeholder="请输入用户名或邮箱"
                    autoComplete="username"
                    allowClear
                  />
                </Form.Item>
                <Form.Item
                  label="密码"
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                >
                  <Input.Password
                    size="large"
                    prefix={<LockOutlined />}
                    placeholder="请输入密码"
                    autoComplete="current-password"
                  />
                </Form.Item>
                {turnstileEnabled ? (
                  <Form.Item>
                    <TurnstileWidget
                      siteKey={turnstileSiteKey}
                      scriptUrl={turnstile.scriptUrl}
                      action="auth_login"
                      onToken={setLoginTurnstileToken}
                    />
                  </Form.Item>
                ) : null}
                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    icon={<LoginOutlined />}
                    loading={submitting}
                    block
                  >
                    登录
                  </Button>
                </Form.Item>
              </Form>
              {oauthProviders.length > 0 && (
                <>
                  <Divider plain style={{ marginBlock: 0 }}>
                    或
                  </Divider>
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    {oauthProviders.map((provider) => (
                      <Button
                        key={provider.provider}
                        size="large"
                        icon={provider.provider === 'GITHUB' ? <GithubOutlined /> : <GoogleOutlined />}
                        loading={submitting}
                        block
                        onClick={() => {
                          window.location.assign(buildOAuthAuthorizeUrl(provider.provider, redirectPath))
                        }}
                      >
                        使用 {provider.label} 登录
                      </Button>
                    ))}
                  </Space>
                </>
              )}
            </>
          )}
          <Flex justify="space-between" align="center">
            <Flex gap={8} align="center">
              <Typography.Text type="secondary">还没有账号？</Typography.Text>
              <Link to="/register" className="theme-link">
                立即注册
              </Link>
            </Flex>
            <Button type="link" onClick={() => setResetOpen(true)} style={{ paddingInline: 0 }}>
              忘记密码？
            </Button>
          </Flex>
        </Space>
      </Card>

      <Modal
        title="找回密码"
        open={resetOpen}
        onCancel={() => {
          setResetOpen(false)
          setResetError(null)
          resetForm.resetFields()
          setResetTurnstileToken(null)
          setResetCountdown(0)
        }}
        onOk={() => resetForm.submit()}
        okText="发送重置链接"
        confirmLoading={resetSending}
        okButtonProps={{ disabled: resetSending || resetCountdown > 0 }}
        destroyOnClose
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Typography.Text type="secondary">
            我们会向你的邮箱发送一条包含重置链接的邮件。
          </Typography.Text>
          {resetError && <Alert type="error" showIcon message={resetError} />}
          <Form
            form={resetForm}
            layout="vertical"
            onFinish={async (values) => {
              await handleSendResetLink(values.email)
            }}
            requiredMark={false}
          >
            {turnstileEnabled ? (
              <Form.Item>
                <TurnstileWidget
                  siteKey={turnstileSiteKey}
                  scriptUrl={turnstile.scriptUrl}
                  action="auth_forgot_password_link"
                  onToken={setResetTurnstileToken}
                />
              </Form.Item>
            ) : null}
            <Form.Item
              label="邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入邮箱地址' },
                { type: 'email', message: '请输入正确的邮箱格式' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="请输入注册邮箱"
                allowClear
              />
            </Form.Item>
            {resetCountdown > 0 && (
              <Typography.Text type="secondary">
                {resetCountdown}s 后可再次发送
              </Typography.Text>
            )}
          </Form>
        </Space>
      </Modal>
    </Flex>
  )
}
