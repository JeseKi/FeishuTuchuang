import { Button, Space, Tag, Typography } from 'antd'
import type { TableColumnsType, FormInstance } from 'antd'
import type { AdminUser, UserRole, UserStatus } from '../../../lib/types'

interface UseColumnsProps {
  currentUserId?: number
  saving: boolean
  deleting: boolean
  editingUserId?: number
  onEdit: (record: AdminUser) => void
  onDelete: (record: AdminUser) => void
  deleteForm: FormInstance
}

export function useColumns({
  currentUserId,
  saving,
  deleting,
  editingUserId,
  onEdit,
  onDelete,
  deleteForm,
}: UseColumnsProps): TableColumnsType<AdminUser> {
  return [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (value: string, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{value}</Typography.Text>
          {record.id === currentUserId && (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              当前登录用户
            </Typography.Text>
          )}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      render: (value: string | null) => value ?? '-',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (value: UserRole) => (
        <Tag color={value === 'admin' ? 'geekblue' : 'default'}>
          {value === 'admin' ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (value: UserStatus) => (
        <Tag color={value === 'active' ? 'green' : 'volcano'}>
          {value === 'active' ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (value: string) => new Date(value).toLocaleString(),
    },
    {
      title: '标识',
      dataIndex: 'id',
      key: 'id',
      render: (value: number) => <Tag color="blue">#{value}</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            onClick={() => onEdit(record)}
            disabled={(saving && editingUserId === record.id) || deleting}
          >
            编辑
          </Button>
          <Button
            size="small"
            danger
            onClick={() => {
              onDelete(record)
              deleteForm.setFieldsValue({ confirmationText: '' })
            }}
            disabled={record.id === currentUserId || deleting}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]
}
