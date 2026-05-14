import { useEffect, useState } from 'react'
import { Button, Descriptions, Flex, Input, Select, Space, Typography, theme } from 'antd'
import {
  CheckCircleOutlined,
  CopyOutlined,
  FileImageOutlined,
  FolderOutlined,
  LinkOutlined,
} from '@ant-design/icons'
import type { FeishuFolder, ImageAsset } from '../../../lib/imageHost'
import { formatBytes, formatDateTime } from './utils'

interface AssetDetailsPanelProps {
  asset: ImageAsset | null
  folders: FeishuFolder[]
  handleMove: (target: ImageAsset, folderId: number) => Promise<void>
  loadingFolders: boolean
  movingId: string | null
  copyText: (text: string, successMessage?: string) => Promise<void>
  copyUrl: (url?: string) => Promise<void>
}

export function AssetDetailsPanel({
  asset,
  folders,
  handleMove,
  loadingFolders,
  movingId,
  copyText,
  copyUrl,
}: AssetDetailsPanelProps) {
  const { token } = theme.useToken()
  const [targetFolderId, setTargetFolderId] = useState<number | undefined>()
  const publicUrl = asset?.url ?? ''
  const markdownImageLink = publicUrl ? `![](${publicUrl})` : ''
  const moving = asset ? movingId === asset.id : false
  const canMove = Boolean(
    asset && targetFolderId && targetFolderId !== asset.feishu_folder_id,
  )

  useEffect(() => {
    setTargetFolderId(asset?.feishu_folder_id ?? undefined)
  }, [asset?.id, asset?.feishu_folder_id])

  return (
    <Flex
      vertical
      gap={12}
      style={{
        flex: '1 1 360px',
        minWidth: 280,
        padding: 16,
        border: `1px solid ${token.colorBorder}`,
        borderRadius: 8,
        background: token.colorBgContainer,
      }}
    >
      <Typography.Title level={4} style={{ margin: 0 }}>
        链接
      </Typography.Title>
      <Typography.Text type="secondary">公开链接</Typography.Text>
      <Input
        value={publicUrl}
        readOnly
        prefix={<LinkOutlined />}
        suffix={
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            disabled={!asset}
            onClick={() => void copyUrl()}
          />
        }
      />
      <Typography.Text type="secondary">Markdown 链接</Typography.Text>
      <Input
        value={markdownImageLink}
        readOnly
        prefix={<LinkOutlined />}
        suffix={
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            disabled={!asset}
            onClick={() => void copyText(markdownImageLink, 'Markdown 链接已复制')}
          />
        }
      />
      <Typography.Text type="secondary">飞书下载 API</Typography.Text>
      <Input
        value={asset?.feishu_download_url ?? ''}
        readOnly
        prefix={<LinkOutlined />}
        suffix={
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            disabled={!asset}
            onClick={() => void copyText(asset?.feishu_download_url ?? '', '飞书链接已复制')}
          />
        }
      />
      <Typography.Text type="secondary">飞书文件 Token</Typography.Text>
      <Input
        value={asset?.feishu_file_token ?? ''}
        readOnly
        prefix={<FileImageOutlined />}
        suffix={
          <Button
            type="text"
            size="small"
            icon={<CopyOutlined />}
            disabled={!asset}
            onClick={() => void copyText(asset?.feishu_file_token ?? '', '飞书 Token 已复制')}
          />
        }
      />
      <Typography.Text type="secondary">移动到文件夹</Typography.Text>
      <Space.Compact block>
        <Select
          value={targetFolderId}
          disabled={!asset || moving}
          loading={loadingFolders}
          placeholder="选择目标文件夹"
          onChange={(folderId?: number) => setTargetFolderId(folderId)}
          style={{ width: '100%' }}
          options={folders.map((folder) => ({
            label: folder.is_active ? `${folder.name}（启用）` : folder.name,
            value: folder.id,
          }))}
        />
        <Button
          icon={<FolderOutlined />}
          loading={moving}
          disabled={!canMove}
          onClick={() => {
            if (asset && targetFolderId) {
              void handleMove(asset, targetFolderId)
            }
          }}
        >
          移动
        </Button>
      </Space.Compact>
      <Descriptions size="small" column={1} bordered>
        <Descriptions.Item label="文件名">
          {asset?.filename ?? '-'}
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          {asset?.mime_type ?? '-'}
        </Descriptions.Item>
        <Descriptions.Item label="大小">
          {asset ? formatBytes(asset.size_bytes) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="文件夹">
          {asset?.feishu_folder_name ?? '-'}
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          {asset ? (
            <Space>
              <CheckCircleOutlined style={{ color: token.colorSuccess }} />
              {asset.reused_existing ? '已复用' : '已上传'}
            </Space>
          ) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="最近访问">
          {formatDateTime(asset?.last_accessed_at)}
        </Descriptions.Item>
      </Descriptions>
    </Flex>
  )
}
