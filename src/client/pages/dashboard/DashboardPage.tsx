import { Button, Card, Flex, Typography } from 'antd'
import { DashboardOutlined, FileImageOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage() {
  const navigate = useNavigate()

  return (
    <Flex vertical gap={16}>
      <Typography.Title level={2} style={{ margin: 0 }}>
        <DashboardOutlined /> 飞书图床概览
      </Typography.Title>
      <Card>
        <Flex align="center" justify="space-between" gap={16} wrap="wrap">
          <div>
            <Typography.Title level={4} style={{ marginTop: 0 }}>
              图片管理
            </Typography.Title>
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              上传图片、配置飞书文件夹、复制公开图片 URL，并通过 API Key 接入外部工具。
            </Typography.Paragraph>
          </div>
          <Button
            type="primary"
            icon={<FileImageOutlined />}
            onClick={() => navigate('/images')}
          >
            打开图床
          </Button>
        </Flex>
      </Card>
    </Flex>
  )
}
