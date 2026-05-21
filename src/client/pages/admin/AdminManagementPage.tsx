import { Tabs } from 'antd'
import AdminSettingsPage from './AdminSettingsPage'
import UserManagementPage from './UserManagementPage'

export default function AdminManagementPage() {
  return (
    <Tabs
      defaultActiveKey="users"
      items={[
        { key: 'users', label: '用户管理', children: <UserManagementPage /> },
        { key: 'settings', label: '系统配置', children: <AdminSettingsPage /> },
      ]}
    />
  )
}
