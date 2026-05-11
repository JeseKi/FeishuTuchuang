import { useMemo, useState, useEffect, useRef } from 'react'
import {
  Avatar,
  Dropdown,
  Flex,
  Layout,
  Menu,
  Modal,
  type MenuProps,
  Typography,
  theme,
  Button,
  Drawer,
} from 'antd'
const { Header, Content, Sider } = Layout
import {
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DashboardOutlined,
  SettingOutlined,
  SafetyOutlined,
  TabletOutlined,
} from '@ant-design/icons'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import ProfilePage from '../../pages/profile/ProfilePage'
import SecurityPage from '../../pages/profile/SecurityPage'
import DevicesPage from '../../pages/profile/DevicesPage'

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()
  const { user, logout, logoutAllDevices } = useAuth()
  const [collapsed, setCollapsed] = useState(true)
  const [isMobile, setIsMobile] = useState(false)
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [settingsActiveKey, setSettingsActiveKey] = useState('profile')
  const [settingsDrawerOpen, setSettingsDrawerOpen] = useState(false)
  const [siderWidth, setSiderWidth] = useState(64)
  const siderRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    if (isMobile) {
      setCollapsed(true)
    }
  }, [isMobile])

  useEffect(() => {
    const siderElement = siderRef.current
    if (!siderElement) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width
        setSiderWidth(width)
      }
    })

    resizeObserver.observe(siderElement)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  const selectedKeys = useMemo(() => {
    if (location.pathname.startsWith('/profile')) {
      if (location.pathname.includes('/security')) {
        return ['security']
      }
      if (location.pathname.includes('/devices')) {
        return ['devices']
      }
      return ['profile']
    }
    if (location.pathname.startsWith('/admin')) {
      return ['admin']
    }
    if (location.pathname === '/example') {
      return ['example']
    }
    if (location.pathname.startsWith('/')) {
      return ['dashboard']
    }
    return []
  }, [location.pathname])

  const menuItems = useMemo<MenuProps['items']>(() => {
    const items: MenuProps['items'] = [
      {
        key: 'dashboard-group',
        icon: <DashboardOutlined />,
        label: '工作台',
        children: [
          {
            key: 'dashboard',
            label: <Link to="/dashboard">首页</Link>,
          },
          {
            key: 'example',
            label: <Link to="/example">示例模块</Link>,
          },
        ],
      },
    ]

    if (user?.role === 'admin') {
      items.push({
        key: 'admin-group',
        icon: <SettingOutlined />,
        label: '管理员',
        children: [
          {
            key: 'admin',
            label: <Link to="/admin">管理员面板</Link>,
          },
        ],
      })
    }

    return items
  }, [user?.role])

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const handleLogoutAllDevices = async () => {
    const confirmed = window.confirm('这会让所有已登录设备立即失效，是否继续？')
    if (!confirmed) {
      return
    }
    await logoutAllDevices()
    navigate('/login', { replace: true })
  }

  const userMenu = useMemo<MenuProps['items']>(
    () => [
      {
        key: 'current-user',
        icon: <UserOutlined />,
        label: (
          <Flex vertical gap={2} style={{ minWidth: 180 }}>
            <Typography.Text type="secondary">当前用户</Typography.Text>
            <Typography.Text strong>{user?.username ?? '未登录'}</Typography.Text>
          </Flex>
        ),
        disabled: true,
      },
      { type: 'divider' },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
      },
    ],
    [user?.username],
  )

  const settingsMenu = useMemo<MenuProps['items']>(() => [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'security',
      icon: <SafetyOutlined />,
      label: '安全',
    },
    {
      key: 'devices',
      icon: <TabletOutlined />,
      label: '设备管理',
    },
  ], [])

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      void handleLogout()
      return
    }
    if (key === 'logout-all') {
      void handleLogoutAllDevices()
    }
  }

  const handleSettingsMenuClick: MenuProps['onClick'] = ({ key }) => {
    setSettingsActiveKey(key)
  }

  const handleMouseEnter = () => {
    if (!isMobile) {
      setCollapsed(false)
    }
  }

  const handleMouseLeave = () => {
    if (!isMobile) {
      setCollapsed(true)
    }
  }

  const toggleCollapsed = () => {
    setCollapsed(!collapsed)
  }

  return (
    <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
      <Sider
        ref={siderRef}
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        collapsedWidth={isMobile ? 0 : 64}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          overflowX: 'hidden',
          overflowY: 'auto',
          background: token.colorBgElevated,
          boxShadow: 'var(--app-header-shadow)',
        }}
        className={isMobile && collapsed ? 'hidden' : ''}
      >
        <Flex
          vertical
          justify="space-between"
          style={{ height: '100%' }}
        >
          <div>
            <Flex
              align="center"
              justify={collapsed ? 'center' : 'space-between'}
              style={{
                height: 56,
                paddingInline: collapsed ? 0 : 16,
                borderBottom: `1px solid ${token.colorBorder}`,
              }}
            >
              {!collapsed && (
                <Link
                  to="/"
                  className="text-base font-semibold"
                  style={{ color: token.colorTextHeading, whiteSpace: 'nowrap' }}
                >
                  Fullstack Template
                </Link>
              )}
              <Button
                type="text"
                icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={toggleCollapsed}
                style={{ marginLeft: collapsed ? 0 : 'auto' }}
              />
            </Flex>
            <Menu
              mode="inline"
              selectedKeys={selectedKeys}
              items={menuItems}
              style={{
                background: 'transparent',
                borderRight: 'none',
                padding: '8px 0',
              }}
            />
          </div>
          <Flex
            align="center"
            justify={collapsed ? 'center' : 'space-between'}
            style={{
              paddingInline: collapsed ? 0 : 16,
              paddingBlock: 12,
              borderTop: `1px solid ${token.colorBorder}`,
            }}
          >
            {collapsed ? (
              <Flex vertical gap={8} align="center">
                <Dropdown
                  menu={{ items: userMenu, onClick: handleUserMenuClick }}
                  placement="topRight"
                  arrow
                  trigger={['hover']}
                  getPopupContainer={() => document.body}
                  overlayStyle={{ zIndex: 1000 }}
                >
                  <Avatar
                    size="small"
                    icon={<UserOutlined />}
                    style={{ background: token.colorPrimary, cursor: 'pointer' }}
                  />
                </Dropdown>
              </Flex>
            ) : (
              <Flex align="center" gap={8} style={{ width: '100%' }}>
                <Dropdown
                  menu={{ items: userMenu, onClick: handleUserMenuClick }}
                  placement="topRight"
                  arrow
                  trigger={['hover']}
                  getPopupContainer={() => document.body}
                  overlayStyle={{ zIndex: 1000 }}
                >
                  <Flex align="center" gap={8} style={{ cursor: 'pointer', flex: 1 }}>
                    <Avatar
                      size="small"
                      icon={<UserOutlined />}
                      style={{ background: token.colorPrimary }}
                    />
                    <Typography.Text ellipsis style={{ flex: 1 }}>
                      {user?.username}
                    </Typography.Text>
                  </Flex>
                </Dropdown>
                {siderWidth > 176 && (
                  <Button
                    type="text"
                    size="small"
                    icon={<SettingOutlined />}
                    onClick={() => setSettingsModalOpen(true)}
                  />
                )}
              </Flex>
            )}
          </Flex>
        </Flex>
      </Sider>
      <Modal
        title={isMobile ? null : '设置'}
        open={settingsModalOpen}
        onCancel={() => {
          setSettingsModalOpen(false)
          setSettingsDrawerOpen(false)
        }}
        footer={null}
        width={isMobile ? '100%' : 1000}
        styles={{
          body: { padding: 0, height: '65vh' },
          ...(isMobile ? { header: { padding: '12px 16px', borderBottom: `1px solid ${token.colorBorder}` }, content: { margin: 0, top: 0, maxWidth: '100vw', borderRadius: 0 } } : {}),
        }}
      >
        <Layout style={{ height: '100%' }}>
          {isMobile ? (
            <>
              {!settingsDrawerOpen && (
                <Flex align="center" gap={8} style={{ padding: '0 16px', borderBottom: `1px solid ${token.colorBorder}` }}>
                  <Button
                    type="text"
                    icon={<MenuUnfoldOutlined />}
                    onClick={() => setSettingsDrawerOpen(true)}
                  />
                  <Typography.Text strong>
                    {settingsActiveKey === 'profile' ? '个人信息' : settingsActiveKey === 'security' ? '安全' : '设备管理'}
                  </Typography.Text>
                </Flex>
              )}
              <Drawer
                open={settingsDrawerOpen}
                onClose={() => setSettingsDrawerOpen(false)}
                placement="left"
                width={200}
                styles={{ body: { padding: 0 } }}
                title="设置"
              >
                <Menu
                  mode="inline"
                  selectedKeys={[settingsActiveKey]}
                  items={settingsMenu}
                  onClick={(e) => {
                    handleSettingsMenuClick(e)
                    setSettingsDrawerOpen(false)
                  }}
                  style={{ border: 'none', background: 'transparent' }}
                />
              </Drawer>
              <Content style={{ padding: '16px', background: token.colorBgContainer, overflow: 'auto' }}>
                {settingsActiveKey === 'profile' && <ProfilePage />}
                {settingsActiveKey === 'security' && <SecurityPage />}
                {settingsActiveKey === 'devices' && <DevicesPage />}
              </Content>
            </>
          ) : (
            <>
              <Sider width={200} style={{ background: token.colorBgContainer, borderRight: `1px solid ${token.colorBorder}` }}>
                <Menu
                  mode="inline"
                  selectedKeys={[settingsActiveKey]}
                  items={settingsMenu}
                  onClick={handleSettingsMenuClick}
                  style={{ border: 'none', background: 'transparent' }}
                />
              </Sider>
              <Content style={{ padding: '32px 40px', background: token.colorBgContainer, overflow: 'auto' }}>
                {settingsActiveKey === 'profile' && <ProfilePage />}
                {settingsActiveKey === 'security' && <SecurityPage />}
                {settingsActiveKey === 'devices' && <DevicesPage />}
              </Content>
            </>
          )}
        </Layout>
      </Modal>
      <Layout
        style={{
          marginLeft: isMobile
            ? 0
            : collapsed
              ? 64
              : 220,
          transition: 'margin-left 0.2s',
        }}
      >
        <Header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 99,
            display: 'flex',
            alignItems: 'center',
            paddingInline: 16,
            paddingBlock: 12,
            background: token.colorBgLayout,
            borderBottom: `1px solid ${token.colorBorder}`,
          }}
        >
          {isMobile && (
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={toggleCollapsed}
            />
          )}
          <Typography.Title
            level={5}
            style={{ margin: 0, flex: 1, marginLeft: isMobile ? 8 : 0 }}
          >
            {selectedKeys[0] === 'admin'
              ? '管理员面板'
              : selectedKeys[0] === 'dashboard'
                ? '工作台'
                : selectedKeys[0] === 'example'
                  ? '示例模块'
                  : ''}
          </Typography.Title>
        </Header>
        <Content style={{ padding: '24px 16px 48px' }}>
          <div
            style={{
              margin: '0 auto',
              maxWidth: 1120,
              width: '100%',
            }}
          >
            <Outlet />
          </div>
        </Content>
      </Layout>
      {isMobile && !collapsed && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 99,
            background: 'rgba(0,0,0,0.5)',
          }}
          onClick={toggleCollapsed}
        />
      )}
    </Layout>
  )
}