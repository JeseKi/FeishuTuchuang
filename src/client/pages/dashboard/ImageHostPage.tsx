import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Descriptions,
  Flex,
  Image,
  Input,
  List,
  Popconfirm,
  Space,
  Spin,
  Typography,
  Upload,
  message,
  theme,
  type UploadProps,
} from 'antd'
import {
  CheckCircleOutlined,
  CopyOutlined,
  DeleteOutlined,
  FileImageOutlined,
  FileOutlined,
  LinkOutlined,
  ReloadOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import {
  createFeishuOAuthAuthorizeUrl,
  deleteImageAsset,
  getFeishuOAuthStatus,
  listImageAssets,
  uploadImageAsset,
  type ImageAsset,
  type FeishuOAuthStatus,
} from '../../lib/imageHost'
import { resolveApiErrorMessage } from '../../lib/error'

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }
  return `${(value / 1024 / 1024).toFixed(2)} MB`
}

function formatDateTime(value?: string): string {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString()
}

export default function ImageHostPage() {
  const { token } = theme.useToken()
  const [asset, setAsset] = useState<ImageAsset | null>(null)
  const [assets, setAssets] = useState<ImageAsset[]>([])
  const [uploading, setUploading] = useState(false)
  const [loadingList, setLoadingList] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [oauthStatus, setOauthStatus] = useState<FeishuOAuthStatus | null>(null)
  const [connectingFeishu, setConnectingFeishu] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messageApi, contextHolder] = message.useMessage()
  const pageSize = 10
  const isVideoAsset = (target?: ImageAsset | null) => target?.mime_type.startsWith('video/') ?? false

  const loadAssets = useCallback(async (targetPage: number) => {
    setLoadingList(true)
    setError(null)
    try {
      const result = await listImageAssets(pageSize, (targetPage - 1) * pageSize)
      setAssets(result.items)
      setTotal(result.total)
      setAsset((current) => current ?? result.items[0] ?? null)
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setLoadingList(false)
    }
  }, [])

  useEffect(() => {
    void loadAssets(1)
  }, [loadAssets])

  const loadOAuthStatus = useCallback(async () => {
    try {
      setOauthStatus(await getFeishuOAuthStatus())
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    }
  }, [])

  useEffect(() => {
    void loadOAuthStatus()
  }, [loadOAuthStatus])

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const result = await uploadImageAsset(file)
      setAsset(result)
      setPage(1)
      await loadAssets(1)
      void messageApi.success(result.reused_existing ? '已复用现有图片' : '上传完成')
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setUploading(false)
    }
  }, [loadAssets, messageApi])

  const handleDelete = async (target: ImageAsset) => {
    setDeletingId(target.id)
    setError(null)
    try {
      await deleteImageAsset(target.id)
      void messageApi.success('图片已删除')
      if (asset?.id === target.id) {
        setAsset(null)
      }
      await loadAssets(page)
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setDeletingId(null)
    }
  }

  const connectFeishuDrive = async () => {
    setConnectingFeishu(true)
    setError(null)
    try {
      const result = await createFeishuOAuthAuthorizeUrl()
      window.open(result.authorize_url, '_blank', 'noopener,noreferrer')
      await navigator.clipboard.writeText(result.callback_url)
      void messageApi.success('已打开飞书授权页，回调地址已复制')
    } catch (err) {
      setError(resolveApiErrorMessage(err))
    } finally {
      setConnectingFeishu(false)
    }
  }

  const uploadProps = useMemo<UploadProps>(() => ({
    accept: 'image/*,video/*',
    maxCount: 1,
    showUploadList: false,
    beforeUpload: (file) => {
      void handleUpload(file)
      return Upload.LIST_IGNORE
    },
  }), [handleUpload])

  const copyUrl = async (url?: string) => {
    const targetUrl = url ?? asset?.url
    if (!targetUrl) return
    await navigator.clipboard.writeText(targetUrl)
    void messageApi.success('链接已复制')
  }

  const copyText = async (text: string, successMessage = '内容已复制') => {
    await navigator.clipboard.writeText(text)
    void messageApi.success(successMessage)
  }

  return (
    <Flex vertical gap={16}>
      {contextHolder}
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
            onClick={connectFeishuDrive}
          >
            {oauthStatus?.connected ? '重新连接飞书' : '连接飞书 Drive'}
          </Button>
          <Button icon={<ReloadOutlined />} loading={loadingList} onClick={() => loadAssets(page)}>
            刷新
          </Button>
          <Upload {...uploadProps}>
            <Button type="primary" icon={<UploadOutlined />} loading={uploading}>
              选择图片/视频
            </Button>
          </Upload>
        </Space>
      </Flex>

      {error && (
        <Alert
          type="error"
          showIcon
          message={error}
          closable
          onClose={() => setError(null)}
        />
      )}

      {oauthStatus && !oauthStatus.connected && (
        <Alert
          type="warning"
          showIcon
          message="尚未连接飞书 Drive，上传、回源和删除需要先完成飞书用户授权。"
        />
      )}

      <Flex gap={16} align="stretch" wrap>
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
            value={asset?.url ?? ''}
            readOnly
            prefix={<LinkOutlined />}
            suffix={
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                disabled={!asset}
                onClick={() => copyUrl()}
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
                onClick={() => copyText(asset?.feishu_download_url ?? '', '飞书链接已复制')}
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
                onClick={() => copyText(asset?.feishu_file_token ?? '', '飞书 Token 已复制')}
              />
            }
          />
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

        <Flex
          align="center"
          justify="center"
          style={{
            flex: '1 1 360px',
            minWidth: 280,
            minHeight: 280,
            padding: 16,
            border: `1px solid ${token.colorBorder}`,
            borderRadius: 8,
            background: token.colorBgContainer,
          }}
        >
          {asset ? (
            isVideoAsset(asset) ? (
              <video
                src={asset.url}
                controls
                style={{
                  width: '100%',
                  maxHeight: 420,
                  objectFit: 'contain',
                }}
              />
            ) : (
              <Image
                src={asset.url}
                alt={asset.original_filename}
                style={{
                  maxHeight: 420,
                  objectFit: 'contain',
                }}
              />
            )
          ) : (
            <FileImageOutlined style={{ fontSize: 64, color: token.colorTextTertiary }} />
          )}
        </Flex>
      </Flex>

      <Flex vertical gap={12}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          历史图片/视频
        </Typography.Title>
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
                    {isVideoAsset(item) ? (
                      <FileOutlined style={{ fontSize: 46, color: token.colorTextTertiary }} />
                    ) : (
                      <Image
                        src={item.url}
                        alt={item.original_filename}
                        preview={false}
                        style={{
                          maxHeight: 150,
                          objectFit: 'contain',
                        }}
                      />
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
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {formatDateTime(item.last_accessed_at)}
                  </Typography.Text>
                  <Space.Compact block>
                    <Button
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={(event) => {
                        event.stopPropagation()
                        void copyUrl(item.url)
                      }}
                      style={{ width: '50%' }}
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
                      style={{ width: '50%' }}
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
    </Flex>
  )
}
