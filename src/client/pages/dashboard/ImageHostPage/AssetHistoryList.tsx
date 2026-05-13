import { Button, Flex, Image, List, Popconfirm, Space, Spin, Tag, Typography, theme } from 'antd'
import {
  CopyOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileImageOutlined,
  FileOutlined,
} from '@ant-design/icons'
import type { ImageAsset } from '../../../lib/imageHost'
import { formatBytes, formatDateTime, isVideoAsset } from './utils'

interface AssetHistoryListProps {
  asset: ImageAsset | null
  assets: ImageAsset[]
  deletingId: string | null
  handleDelete: (asset: ImageAsset) => Promise<void>
  loadAssets: (page: number) => Promise<void>
  loadingList: boolean
  page: number
  pageSize: number
  previewAssetId: string | null
  setAsset: (asset: ImageAsset) => void
  setPage: (page: number) => void
  setPreviewAssetId: (assetId: string) => void
  total: number
  copyText: (text: string, successMessage?: string) => Promise<void>
  copyUrl: (url?: string) => Promise<void>
}

export function AssetHistoryList({
  asset,
  assets,
  deletingId,
  handleDelete,
  loadAssets,
  loadingList,
  page,
  pageSize,
  previewAssetId,
  setAsset,
  setPage,
  setPreviewAssetId,
  total,
  copyText,
  copyUrl,
}: AssetHistoryListProps) {
  const { token } = theme.useToken()

  return (
    <Flex vertical gap={12}>
      <Spin spinning={loadingList}>
        <List
          grid={{
            gutter: 12,
            xs: 1,
            sm: 2,
            md: 3,
            lg: 4,
            xl: 5,
            xxl: 6,
          }}
          dataSource={assets}
          locale={{ emptyText: '暂无图片或视频' }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: false,
            onChange: (nextPage) => {
              setPage(nextPage)
              void loadAssets(nextPage)
            },
          }}
          renderItem={(item) => (
            <List.Item>
              <Flex
                vertical
                gap={8}
                onClick={() => setAsset(item)}
                style={{
                  height: 280,
                  padding: 10,
                  border: `1px solid ${asset?.id === item.id ? token.colorPrimary : token.colorBorder}`,
                  borderRadius: 8,
                  background: token.colorBgContainer,
                  cursor: 'pointer',
                }}
              >
                <Flex
                  align="center"
                  justify="center"
                  style={{
                    height: 150,
                    overflow: 'hidden',
                    background: token.colorFillQuaternary,
                    borderRadius: 6,
                  }}
                >
                  {previewAssetId === item.id && !isVideoAsset(item) ? (
                    <Image
                      src={item.url}
                      alt={item.original_filename}
                      preview={false}
                      style={{
                        maxHeight: 150,
                        objectFit: 'contain',
                      }}
                    />
                  ) : previewAssetId === item.id && isVideoAsset(item) ? (
                    <video
                      src={item.url}
                      muted
                      playsInline
                      preload="metadata"
                      style={{
                        width: '100%',
                        maxHeight: 150,
                        objectFit: 'contain',
                      }}
                    />
                  ) : isVideoAsset(item) ? (
                    <FileOutlined style={{ fontSize: 46, color: token.colorTextTertiary }} />
                  ) : (
                    <FileImageOutlined style={{ fontSize: 46, color: token.colorTextTertiary }} />
                  )}
                </Flex>
                <Typography.Text
                  ellipsis={{ tooltip: item.original_filename }}
                  style={{ fontSize: 13 }}
                >
                  {item.original_filename}
                </Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {formatBytes(item.size_bytes)}
                </Typography.Text>
                <Flex style={{ minHeight: 22 }}>
                  {item.feishu_folder_name && <Tag>{item.feishu_folder_name}</Tag>}
                </Flex>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  {formatDateTime(item.last_accessed_at)}
                </Typography.Text>
                <Space.Compact block>
                  <Button
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={(event) => {
                      event.stopPropagation()
                      setAsset(item)
                      setPreviewAssetId(item.id)
                    }}
                    style={{ width: '34%' }}
                  >
                    预览
                  </Button>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={(event) => {
                      event.stopPropagation()
                      void copyUrl(item.url)
                    }}
                    style={{ width: '33%' }}
                  >
                    公开
                  </Button>
                  <Button
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={(event) => {
                      event.stopPropagation()
                      void copyText(item.feishu_file_token, '飞书 Token 已复制')
                    }}
                    style={{ width: '33%' }}
                  >
                    飞书
                  </Button>
                </Space.Compact>
                <Popconfirm
                  title="删除文件"
                  description="将尝试同时删除飞书侧资源。"
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                  onConfirm={(event) => {
                    event?.stopPropagation()
                    void handleDelete(item)
                  }}
                  onCancel={(event) => event?.stopPropagation()}
                >
                  <Button
                    danger
                    block
                    size="small"
                    icon={<DeleteOutlined />}
                    loading={deletingId === item.id}
                    onClick={(event) => event.stopPropagation()}
                  >
                    删除
                  </Button>
                </Popconfirm>
              </Flex>
            </List.Item>
          )}
        />
      </Spin>
    </Flex>
  )
}
