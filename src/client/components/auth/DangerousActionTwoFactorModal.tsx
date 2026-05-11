import { Alert, Form, Input, Modal, Space, Typography } from 'antd'
import { useCallback, useEffect, useState } from 'react'

interface DangerousActionTwoFactorModalProps {
  open: boolean
  title: string
  description: string
  loading?: boolean
  onCancel: () => void
  onConfirm: (code: string) => Promise<void> | void
}

interface FormValues {
  code: string
}

export default function DangerousActionTwoFactorModal({
  open,
  title,
  description,
  loading = false,
  onCancel,
  onConfirm,
}: DangerousActionTwoFactorModalProps) {
  const [form] = Form.useForm<FormValues>()
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    if (!open) {
      form.resetFields()
    }
  }, [form, open])

  const handleOk = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await onConfirm(values.code.trim())
    } catch {
      return
    }
  }, [form, onConfirm])

  return (
    <Modal
      title={title}
      open={open}
      onCancel={onCancel}
      onOk={() => void handleOk()}
      okText="验证并继续"
      confirmLoading={loading}
      destroyOnClose
      width={isMobile ? '95%' : 520}
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Alert
          type="warning"
          showIcon
          message="该操作需要二步验证"
          description={description}
        />
        <Typography.Text type="secondary">
          支持输入当前 TOTP 验证码，或尚未使用过的 backup code。
        </Typography.Text>
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            label="验证码 / Backup Code"
            name="code"
            rules={[{ required: true, message: '请输入验证码或 backup code' }]}
          >
            <Input placeholder="请输入验证码或 backup code" autoFocus />
          </Form.Item>
        </Form>
      </Space>
    </Modal>
  )
}
