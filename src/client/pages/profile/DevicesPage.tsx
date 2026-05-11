import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, Card, Space, Typography } from 'antd'
import { useAuth } from '../../hooks/useAuth'
import { resolveApiErrorMessage } from '../../lib/error'

export default function DevicesPage() {
  const navigate = useNavigate()
  const { logoutAllDevices } = useAuth()
  const { message } = App.useApp()

  const [submitting, setSubmitting] = useState(false)

  const handleLogoutAllDevices = async () => {
    const confirmed = window.confirm('这会让所有已登录设备立即失效，是否继续？')
    if (!confirmed) {
      return
    }
    setSubmitting(true)
    try {
      await logoutAllDevices()
      message.success('已退出所有设备')
      navigate('/login', { replace: true })
    } catch (error) {
      const text = resolveApiErrorMessage(error)
      message.error(text)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Space direction="vertical" size={24} style={{ width: '100%' }}>
      <Card bordered={false}>
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Typography.Title level={4} style={{ marginBottom: 0 }}>
            退出所有设备
          </Typography.Title>
          <Typography.Text type="secondary">
            这会让所有已登录设备立即失效，您需要重新登录所有设备。
          </Typography.Text>
          <Button
            danger
            loading={submitting}
            onClick={() => void handleLogoutAllDevices()}
          >
            退出所有设备
          </Button>
        </Space>
      </Card>
    </Space>
  )
}
