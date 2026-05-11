import { Alert, Descriptions, Modal, Space, Typography } from 'antd'
import type { OAuthClientWithSecret } from '../../../lib/types'

interface SecretModalProps {
  secretResult: OAuthClientWithSecret | null
  isMobile: boolean
  onClose: () => void
}

export default function SecretModal({ secretResult, isMobile, onClose }: SecretModalProps) {
  return (
    <Modal
      title="Client 凭据"
      open={Boolean(secretResult)}
      onCancel={onClose}
      onOk={onClose}
      okText="关闭"
      cancelButtonProps={{ style: { display: 'none' } }}
      width={isMobile ? '95%' : 640}
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Alert type="warning" showIcon message="Client Secret 只会显示这一次，请立即保存。" />
        <Typography.Text strong>{secretResult?.name}</Typography.Text>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Client ID">
            <Typography.Text code copyable style={{ wordBreak: 'break-all' }}>
              {secretResult?.client_id}
            </Typography.Text>
          </Descriptions.Item>
          <Descriptions.Item label="Client Secret">
            <Typography.Text code copyable style={{ wordBreak: 'break-all' }}>
              {secretResult?.client_secret}
            </Typography.Text>
          </Descriptions.Item>
        </Descriptions>
      </Space>
    </Modal>
  )
}
