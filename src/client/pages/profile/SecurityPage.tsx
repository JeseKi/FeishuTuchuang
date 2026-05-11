import {
  Alert,
  App,
  Button,
  Card,
  Flex,
  Form,
  Input,
  QRCode,
  Space,
  Typography,
} from 'antd'
import {
  LockOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { resolveApiErrorMessage } from '../../lib/error'

export default function SecurityPage() {
  const {
    user,
    sendPasswordChangeLink,
    startTwoFactorSetup,
    confirmTwoFactorSetup,
    disableTwoFactor,
  } = useAuth()
  const { message } = App.useApp()

  const [twoFactorSetupForm] = Form.useForm<{ code: string }>()
  const [disableTwoFactorForm] = Form.useForm<{ password: string; code: string }>()

  const [passwordSending, setPasswordSending] = useState(false)
  const [passwordCountdown, setPasswordCountdown] = useState(0)
  const [passwordHint, setPasswordHint] = useState<string | null>(null)
  const [twoFactorSetupData, setTwoFactorSetupData] = useState<{
    secret: string
    secret_masked: string
    otpauth_url: string
    setup_token: string
  } | null>(null)
  const [twoFactorSetupLoading, setTwoFactorSetupLoading] = useState(false)
  const [twoFactorSetupError, setTwoFactorSetupError] = useState<string | null>(null)
  const [disableTwoFactorLoading, setDisableTwoFactorLoading] = useState(false)
  const [disableTwoFactorError, setDisableTwoFactorError] = useState<string | null>(null)

  useEffect(() => {
    if (passwordCountdown <= 0) {
      return
    }

    const timer = window.setInterval(() => {
      setPasswordCountdown((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)

    return () => window.clearInterval(timer)
  }, [passwordCountdown])

  const handleSendPasswordLink = async () => {
    if (passwordSending || passwordCountdown > 0) {
      return
    }

    const performSend = async (twoFactorCode?: string) => {
      setPasswordSending(true)
      setPasswordHint(null)
      try {
        await sendPasswordChangeLink(twoFactorCode)
        setPasswordCountdown(60)
        setPasswordHint('确认链接已发送到当前邮箱，请打开邮件中的页面设置新密码。')
        message.success('确认链接已发送')
      } catch (error) {
        const text = resolveApiErrorMessage(error, '确认链接发送失败，请稍后重试。')
        setPasswordHint(text)
        message.error(text)
      } finally {
        setPasswordSending(false)
      }
    }

    if (user?.two_factor_enabled) {
      return
    }

    await performSend()
  }

  const handleStartTwoFactor = async () => {
    setTwoFactorSetupLoading(true)
    setTwoFactorSetupError(null)
    try {
      const result = await startTwoFactorSetup()
      setTwoFactorSetupData(result)
      twoFactorSetupForm.resetFields()
    } catch (error) {
      const text = resolveApiErrorMessage(error, '2FA 初始化失败，请稍后重试。')
      setTwoFactorSetupError(text)
      message.error(text)
    } finally {
      setTwoFactorSetupLoading(false)
    }
  }

  const handleConfirmTwoFactorSetup = async (values: { code: string }) => {
    if (!twoFactorSetupData) {
      return
    }
    setTwoFactorSetupLoading(true)
    setTwoFactorSetupError(null)
    try {
      await confirmTwoFactorSetup({
        setup_token: twoFactorSetupData.setup_token,
        code: values.code.trim(),
      })
      setTwoFactorSetupData(null)
      twoFactorSetupForm.resetFields()
      message.success('2FA 已开启')
    } catch (error) {
      const text = resolveApiErrorMessage(error, '2FA 验证失败，请稍后重试。')
      setTwoFactorSetupError(text)
      message.error(text)
    } finally {
      setTwoFactorSetupLoading(false)
    }
  }

  const handleDisableTwoFactor = async (values: { password: string; code: string }) => {
    setDisableTwoFactorLoading(true)
    setDisableTwoFactorError(null)
    try {
      const { message: msg } = await disableTwoFactor({
        password: values.password,
        code: values.code.trim(),
      })
      disableTwoFactorForm.resetFields()
      message.success(msg)
    } catch (error) {
      const text = resolveApiErrorMessage(error, '关闭 2FA 失败，请稍后重试。')
      setDisableTwoFactorError(text)
      message.error(text)
    } finally {
      setDisableTwoFactorLoading(false)
    }
  }

  return (
    <Space direction="vertical" size={40} style={{ width: '100%' }}>
      <Card title="密码修改" bordered={false}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <Typography.Text type="secondary">
            系统会向当前邮箱发送一个确认链接。打开该页面后，才能设置新的登录密码。
          </Typography.Text>
          <Space align="center" size={16}>
            <Typography.Text type="secondary">确认邮件发送至</Typography.Text>
            <Typography.Text strong>{user?.email ?? '-'}</Typography.Text>
          </Space>
          <Button
            type="primary"
            icon={<LockOutlined />}
            loading={passwordSending}
            disabled={passwordCountdown > 0}
            onClick={() => void handleSendPasswordLink()}
            size="large"
          >
            {passwordCountdown > 0 ? `${passwordCountdown}s 后可重发` : '发送确认链接'}
          </Button>
          {passwordHint && <Alert type="info" showIcon message={passwordHint} />}
        </Space>
      </Card>

      <Card title="双因素认证" bordered={false}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <Space align="center" size={16}>
            <Typography.Text type="secondary">当前状态</Typography.Text>
            <Typography.Text strong>
              {user?.two_factor_enabled ? '已开启' : '未开启'}
            </Typography.Text>
          </Space>

          {!user?.two_factor_enabled && (
            <Button
              type="primary"
              icon={<SafetyCertificateOutlined />}
              loading={twoFactorSetupLoading && !twoFactorSetupData}
              onClick={() => void handleStartTwoFactor()}
              size="large"
            >
              开始设置 2FA
            </Button>
          )}

          {user?.two_factor_enabled ? (
            <Space direction="vertical" size={24} style={{ width: '100%' }}>
              <Typography.Text type="secondary">
                您的账号已启用 TOTP 双因素认证。登录时需要额外输入动态码或 backup code。
              </Typography.Text>
              {disableTwoFactorError && <Alert type="error" showIcon message={disableTwoFactorError} />}
              <Form
                form={disableTwoFactorForm}
                layout="vertical"
                onFinish={handleDisableTwoFactor}
                requiredMark={false}
              >
                <Form.Item
                  label="当前密码"
                  name="password"
                  rules={[{ required: true, message: '请输入当前密码' }]}
                  style={{ marginBottom: 24 }}
                >
                  <Input.Password
                    prefix={<LockOutlined />}
                    placeholder="请输入当前密码"
                    autoComplete="current-password"
                    size="large"
                  />
                </Form.Item>
                <Form.Item
                  label="动态码"
                  name="code"
                  rules={[
                    { required: true, message: '请输入动态码或 backup code' },
                    { min: 6, message: '请输入有效的动态码或 backup code' },
                  ]}
                  style={{ marginBottom: 24 }}
                >
                  <Input
                    prefix={<SafetyCertificateOutlined />}
                    placeholder="验证码或 backup code"
                    allowClear
                    size="large"
                  />
                </Form.Item>
                <Form.Item style={{ marginBottom: 0 }}>
                  <Button danger htmlType="submit" loading={disableTwoFactorLoading} size="large">
                    关闭 2FA
                  </Button>
                </Form.Item>
              </Form>
            </Space>
          ) : (
            <Space direction="vertical" size={24} style={{ width: '100%' }}>
              <Typography.Text type="secondary">
                推荐使用 Google Authenticator、1Password 或 Microsoft Authenticator 扫描二维码后，再输入一次验证码完成绑定。
              </Typography.Text>
              {twoFactorSetupError && <Alert type="error" showIcon message={twoFactorSetupError} />}
              {twoFactorSetupData && (
                <Card size="small" bordered={false} className="theme-subtle-surface">
                  <Flex gap={32} align="middle" wrap="wrap">
                    <Flex justify="center" style={{ flex: '0 0 auto' }}>
                      <QRCode value={twoFactorSetupData.otpauth_url} size={180} />
                    </Flex>
                    <div style={{ flex: 1, minWidth: 280 }}>
                      <Space direction="vertical" size={16} style={{ width: '100%' }}>
                        <Typography.Text>
                          手动输入密钥：
                          <Typography.Text copyable={{ text: twoFactorSetupData.secret }} style={{ marginLeft: 8 }}>
                            {twoFactorSetupData.secret}
                          </Typography.Text>
                        </Typography.Text>
                        <Typography.Text type="secondary">
                          如无法扫码，可手动录入密钥。当前展示摘要：{twoFactorSetupData.secret_masked}
                        </Typography.Text>
                        <Form
                          form={twoFactorSetupForm}
                          layout="vertical"
                          onFinish={handleConfirmTwoFactorSetup}
                          requiredMark={false}
                        >
                          <Form.Item
                            label="应用中的 6 位验证码"
                            name="code"
                            rules={[
                              { required: true, message: '请输入动态码' },
                              { len: 6, message: '动态码应为 6 位' },
                            ]}
                            style={{ marginBottom: 24 }}
                          >
                            <Input
                              prefix={<SafetyCertificateOutlined />}
                              placeholder="请输入应用中当前显示的验证码"
                              maxLength={6}
                              allowClear
                              size="large"
                            />
                          </Form.Item>
                          <Form.Item style={{ marginBottom: 0 }}>
                            <Space>
                              <Button type="primary" htmlType="submit" loading={twoFactorSetupLoading} size="large">
                                确认开启 2FA
                              </Button>
                              <Button
                                onClick={() => {
                                  setTwoFactorSetupData(null)
                                  setTwoFactorSetupError(null)
                                  twoFactorSetupForm.resetFields()
                                }}
                              >
                                取消本次设置
                              </Button>
                            </Space>
                          </Form.Item>
                        </Form>
                      </Space>
                    </div>
                  </Flex>
                </Card>
              )}
            </Space>
          )}
        </Space>
      </Card>
    </Space>
  )
}
