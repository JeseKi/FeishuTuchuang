import { Button, Flex, List, Popconfirm, Space, Spin, Tag, Typography, theme } from 'antd'
import {
  DeleteOutlined,
  EditOutlined,
  FolderOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { FeishuFolder } from '../../../lib/imageHost'

interface FolderSectionProps {
  activeFolder: FeishuFolder | null
  folders: FeishuFolder[]
  loadingFolders: boolean
  loadFolders: () => Promise<void>
  openCreateFolderModal: () => void
  openEditFolderModal: (folder: FeishuFolder) => void
  removeFolder: (folder: FeishuFolder) => Promise<void>
}

export function FolderSection({
  activeFolder,
  folders,
  loadingFolders,
  loadFolders,
  openCreateFolderModal,
  openEditFolderModal,
  removeFolder,
}: FolderSectionProps) {
  const { token } = theme.useToken()

  return (
    <Flex
      vertical
      gap={12}
      style={{
        padding: 16,
        border: `1px solid ${token.colorBorder}`,
        borderRadius: 8,
        background: token.colorBgContainer,
      }}
    >
      <Flex align="center" justify="space-between" wrap gap={12}>
        <Space>
          <FolderOutlined style={{ color: token.colorPrimary }} />
          <Typography.Title level={4} style={{ margin: 0 }}>
            飞书文件夹
          </Typography.Title>
          {activeFolder && <Tag color="green">当前：{activeFolder.name}</Tag>}
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} loading={loadingFolders} onClick={() => void loadFolders()}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateFolderModal}>
            新增
          </Button>
        </Space>
      </Flex>
      <Spin spinning={loadingFolders}>
        <List
          dataSource={folders}
          locale={{ emptyText: '暂无文件夹配置' }}
          renderItem={(folder) => (
            <List.Item
              actions={[
                <Button
                  key="edit"
                  size="small"
                  icon={<EditOutlined />}
                  onClick={() => openEditFolderModal(folder)}
                />,
                <Popconfirm
                  key="delete"
                  title="删除文件夹配置"
                  description="不会删除飞书 Drive 中的文件夹或文件。"
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                  onConfirm={() => void removeFolder(folder)}
                >
                  <Button danger size="small" icon={<DeleteOutlined />} />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<FolderOutlined style={{ color: token.colorPrimary, fontSize: 20 }} />}
                title={(
                  <Space wrap>
                    <Typography.Text strong>{folder.name}</Typography.Text>
                    {folder.is_active && <Tag color="green">启用</Tag>}
                  </Space>
                )}
                description={folder.folder_token}
              />
            </List.Item>
          )}
        />
      </Spin>
    </Flex>
  )
}
