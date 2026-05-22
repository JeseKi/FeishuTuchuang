import { useNavigate } from 'react-router-dom'
import { Avatar, Button, Dropdown, Flex, Tag, Typography } from 'antd'
import {
  ApiOutlined,
  CloudServerOutlined,
  FileImageOutlined,
  LogoutOutlined,
  SafetyOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useAuth } from '../../hooks/useAuth'

const features = [
  {
    icon: <FileImageOutlined className="text-3xl text-blue-500" />,
    title: '飞书 Drive 冷存储',
    desc: '图片上传后存入飞书云空间，本机磁盘只保留热缓存。',
  },
  {
    icon: <ApiOutlined className="text-3xl text-green-500" />,
    title: '稳定图片 URL',
    desc: '对外提供 /i/{filename} 访问地址，并支持 API Key 集成上传。',
  },
  {
    icon: <SafetyOutlined className="text-3xl text-purple-500" />,
    title: '自托管账号体系',
    desc: '默认关闭公开注册，由管理员创建用户和管理访问权限。',
  },
  {
    icon: <CloudServerOutlined className="text-3xl text-cyan-500" />,
    title: '轻量部署',
    desc: 'FastAPI 托管 API 与前端构建产物，SQLite 即可运行。',
  },
]

const techStack = [
  'FastAPI',
  'React',
  'SQLite',
  'Alembic',
  'Feishu Drive',
  'API Key',
  'TOTP 2FA',
]

export default function LandingPage() {
  const navigate = useNavigate()
  const { isAuthenticated, user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/', { replace: true })
  }

  const userMenuItems = [
    {
      key: 'user',
      icon: <UserOutlined />,
      label: (
        <Flex vertical gap={2} style={{ minWidth: 160 }}>
          <Typography.Text type="secondary">当前用户</Typography.Text>
          <Typography.Text strong>{user?.username ?? '未登录'}</Typography.Text>
        </Flex>
      ),
      disabled: true,
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <div className="min-h-screen bg-[var(--app-bg)] text-[var(--app-text-primary)] transition-colors duration-300">
      <header className="fixed top-0 w-full z-50 bg-[var(--app-elevated-bg)] backdrop-blur-md border-b border-[var(--app-border-color)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xl font-bold tracking-tight">
            <img src="/logo.svg" alt="飞书图床" className="h-8 w-8" />
            <span>飞书图床</span>
          </div>
          {isAuthenticated ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
              <Avatar
                icon={<UserOutlined />}
                style={{ background: '#1668dc', cursor: 'pointer' }}
              />
            </Dropdown>
          ) : (
            <Button type="primary" size="small" onClick={() => navigate('/login')}>
              登录
            </Button>
          )}
        </div>
      </header>

      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Tag color="blue" className="mb-4">自托管飞书图床</Tag>
          <img src="/logo.svg" alt="飞书图床" className="mb-6 h-20 w-20" />
          <Typography.Title level={1} className="!mb-6">
            用飞书云空间托管图片
          </Typography.Title>
          <Typography.Paragraph className="!text-lg !text-[var(--app-text-secondary)] max-w-2xl !mb-8">
            面向个人和小团队的开源图床服务。图片写入飞书 Drive，本地缓存加速公开访问，
            保留数据控制权，同时避免额外维护对象存储。
          </Typography.Paragraph>
          <Flex gap={12} wrap="wrap">
            <Button
              type="primary"
              size="large"
              icon={<FileImageOutlined />}
              onClick={() => navigate(isAuthenticated ? '/images' : '/login')}
            >
              {isAuthenticated ? '进入图床' : '登录管理'}
            </Button>
            {isAuthenticated && (
              <Button size="large" onClick={() => navigate('/dashboard')}>
                查看概览
              </Button>
            )}
          </Flex>
          {!isAuthenticated && (
            <Typography.Paragraph className="!mt-4 !text-sm !text-[var(--app-text-secondary)]">
              默认关闭公开注册，请使用管理员创建的账号登录。
            </Typography.Paragraph>
          )}
        </div>
      </section>

      <section className="py-10 px-4 sm:px-6 lg:px-8 border-y border-[var(--app-border-color)]">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap gap-2">
            {techStack.map((tech) => (
              <Tag key={tech} className="text-sm py-1 px-3">
                {tech}
              </Tag>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-lg bg-[var(--app-elevated-bg)] border border-[var(--app-border-color)] theme-card-shadow"
            >
              <div className="mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-[var(--app-text-secondary)] leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-[var(--app-border-color)]">
        <div className="max-w-7xl mx-auto text-sm text-[var(--app-text-secondary)]">
          <p>MIT Licensed. Built for self-hosted Feishu image hosting.</p>
        </div>
      </footer>
    </div>
  )
}
