import { Button, Flex, Space, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import { DeleteOutlined, EditOutlined, KeyOutlined } from '@ant-design/icons'
import type { OAuthClient } from '../../../lib/types'

interface UseColumnsParams {
  saving: boolean
  onEdit: (client: OAuthClient) => void
  onResetSecret: (client: OAuthClient) => void
  onDelete: (client: OAuthClient) => void
}

export function useColumns({
  saving,
  onEdit,
  onResetSecret,
  onDelete,
}: UseColumnsParams): TableColumnsType<OAuthClient> {
  return [
    {
      title: '应用',
      key: 'client',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{record.name}</Typography.Text>
          <Typography.Text code copyable>{record.client_id}</Typography.Text>
        </Space>
      ),
    },
    {
      title: 'Redirect URIs',
      key: 'redirect_uris',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          {record.redirect_uris.map((uri) => (
            <Typography.Text key={uri} type="secondary">{uri}</Typography.Text>
          ))}
        </Space>
      ),
    },
    {
      title: 'Scopes',
      key: 'allowed_scopes',
      render: (_, record) => (
        <Flex gap={6} wrap="wrap">
          {record.allowed_scopes.map((scope) => <Tag key={scope}>{scope}</Tag>)}
        </Flex>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record) => (
        <Space>
          <Tag color={record.is_active ? 'green' : 'default'}>{record.is_active ? '启用' : '停用'}</Tag>
          <Tag color={record.require_pkce ? 'blue' : 'volcano'}>{record.require_pkce ? 'PKCE' : '无 PKCE'}</Tag>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space wrap>
          <Button size="small" icon={<EditOutlined />} onClick={() => onEdit(record)} disabled={saving}>
            编辑
          </Button>
          <Button size="small" icon={<KeyOutlined />} onClick={() => onResetSecret(record)} disabled={saving}>
            重置 Secret
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => onDelete(record)} disabled={saving}>
            删除
          </Button>
        </Space>
      ),
    },
  ]
}
