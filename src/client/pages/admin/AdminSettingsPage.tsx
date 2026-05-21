import { Alert, App, Button, Card, Flex, Form, Input, Space, Typography } from 'antd'
import { ReloadOutlined, SaveOutlined, SettingOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useState } from 'react'
import DangerousActionTwoFactorModal from '../../components/auth/DangerousActionTwoFactorModal'
import { getAdminSettings, updateAdminSettings } from '../../lib/admin'
import { resolveApiErrorMessage } from '../../lib/error'

interface SettingsFormValues {
  image_cors_allowed_origin: string
}

export default function AdminSettingsPage() {
  const { message } = App.useApp()
  const [form] = Form.useForm<SettingsFormValues>()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [twoFactorOpen, setTwoFactorOpen] = useState(false)

  const loadSettings = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getAdminSettings()
      form.setFieldsValue(data)
    } catch (err) {
      const text = resolveApiErrorMessage(err, '读取配置失败，请稍后再试。')
      setError(text)
      message.error(text)
    } finally {
      setLoading(false)
    }
  }, [form, message])

  useEffect(() => { void loadSettings() }, [loadSettings])

  const saveSettings = useCallback(async (twoFactorCode?: string) => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      const updated = await updateAdminSettings(
        {
          image_cors_allowed_origin: values.image_cors_allowed_origin.trim(),
        },
        twoFactorCode,
      )
      form.setFieldsValue(updated)
      setTwoFactorOpen(false)
      message.success('系统配置已更新')
    } catch (err) {
      const text = resolveApiErrorMessage(err, '保存配置失败，请稍后再试。')
      if (text === '危险操作需要二步验证') {
        setTwoFactorOpen(true)
      } else {
        message.error(text)
      }
    } finally {
      setSaving(false)
    }
  }, [form, message])

  return (
    <Flex vertical gap={24}>
      <Card>
        <Flex align="center" justify="space-between" wrap="wrap" gap={16}>
          <Space>
            <SettingOutlined style={{ fontSize: 20 }} />
            <Typography.Title level={4} style={{ margin: 0 }}>系统配置</Typography.Title>
          </Space>
          <Button icon={<ReloadOutlined />} onClick={loadSettings} loading={loading}>刷新</Button>
        </Flex>
        <Typography.Paragraph type="secondary" className="mt-4">
          配置公开图片响应头，便于前端直接 fetch 图片二进制并打包下载。
        </Typography.Paragraph>
      </Card>

      {error && <Alert type="error" showIcon message={error} />}

      <Card title="图片源 CORS">
        <Form form={form} layout="vertical" initialValues={{ image_cors_allowed_origin: '*' }}>
          <Form.Item
            label="Access-Control-Allow-Origin"
            name="image_cors_allowed_origin"
            extra="默认 *。如需收紧权限，可填写前端站点 Origin，例如 https://43.139.69.53:20194。"
            rules={[{ required: true, message: '请输入图片 CORS 允许源' }]}
          >
            <Input placeholder="*" maxLength={500} />
          </Form.Item>
          <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={() => void saveSettings()}>
            保存配置
          </Button>
        </Form>
      </Card>

      <DangerousActionTwoFactorModal
        open={twoFactorOpen}
        title="二步验证后保存配置"
        description="管理员配置会影响公开图片跨域访问，请先完成二步验证。"
        loading={saving}
        onCancel={() => setTwoFactorOpen(false)}
        onConfirm={async (code) => { await saveSettings(code) }}
      />
    </Flex>
  )
}
