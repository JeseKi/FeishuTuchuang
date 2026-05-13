import { Button, Flex, Space, Typography, Upload, theme, type UploadProps } from 'antd'
import {
  FileImageOutlined,
  LinkOutlined,
  ReloadOutlined,
  SnippetsOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import type { FeishuOAuthStatus } from '../../../lib/imageHost'

interface HeaderActionsProps {
  connectingFeishu: boolean
  handleClipboardUpload: () => void
  loadAssets: (page: number) => Promise<void>
  loadingList: boolean
  oauthStatus: FeishuOAuthStatus | null
  page: number
  uploadProps: UploadProps
  uploading: boolean
  connectFeishuDrive: () => Promise<void>
}

export function HeaderActions({
  connectingFeishu,
  handleClipboardUpload,
  loadAssets,
  loadingList,
  oauthStatus,
  page,
  uploadProps,
  uploading,
  connectFeishuDrive,
}: HeaderActionsProps) {
  const { token } = theme.useToken()

  return (
    <Flex align="center" justify="space-between" wrap gap={12}>
      <Space size={10}>
        <FileImageOutlined style={{ color: token.colorPrimary, fontSize: 24 }} />
        <Typography.Title level={2} style={{ margin: 0 }}>
          飞书图床
        </Typography.Title>
      </Space>
      <Space wrap>
        <Button
          icon={<LinkOutlined />}
          loading={connectingFeishu}
          onClick={() => void connectFeishuDrive()}
        >
          {oauthStatus?.connected ? '重新连接飞书' : '连接飞书 Drive'}
        </Button>
        <Button icon={<ReloadOutlined />} loading={loadingList} onClick={() => void loadAssets(page)}>
          刷新
        </Button>
        <Button
          icon={<SnippetsOutlined />}
          loading={uploading}
          onClick={() => void handleClipboardUpload()}
        >
          剪贴板上传
        </Button>
        <Upload {...uploadProps}>
          <Button type="primary" icon={<UploadOutlined />} loading={uploading}>
            选择图片/视频
          </Button>
        </Upload>
      </Space>
    </Flex>
  )
}
