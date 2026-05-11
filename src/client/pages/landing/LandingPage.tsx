import { useNavigate } from 'react-router-dom'
import { Button, Tag, Avatar, Dropdown, Flex, Typography } from 'antd'
import { RocketOutlined, SafetyOutlined, ThunderboltOutlined, ToolOutlined, GlobalOutlined, MobileOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons'
import { useAuth } from '../../hooks/useAuth'

const features = [
  {
    icon: <ThunderboltOutlined className="text-3xl text-blue-500" />,
    title: 'FastAPI + React',
    desc: '现代化全栈技术栈，开箱即用',
  },
  {
    icon: <SafetyOutlined className="text-3xl text-green-500" />,
    title: '完整的认证系统',
    desc: 'JWT + TOTP 双因素认证，设备管理中',
  },
  {
    icon: <ToolOutlined className="text-3xl text-purple-500" />,
    title: '模块化架构',
    desc: '参考 example_module，快速开发业务模块',
  },
  {
    icon: <GlobalOutlined className="text-3xl text-cyan-500" />,
    title: '暗色/亮色主题',
    desc: '内置主题切换，Tailwind CSS 4 + Ant Design',
  },
  {
    icon: <MobileOutlined className="text-3xl text-orange-500" />,
    title: '响应式设计',
    desc: '移动优先，自适应各种屏幕尺寸',
  },
  {
    icon: <RocketOutlined className="text-3xl text-red-500" />,
    title: '快速开发',
    desc: 'Vite 构建，热更新，开发体验极佳',
  },
]

const techStack = [
  'React 19', 'TypeScript', 'Vite', 'Tailwind CSS 4',
  'Ant Design 5', 'FastAPI', 'SQLAlchemy', 'Pydantic',
  'JWT Auth', 'TOTP 2FA', 'Alembic', 'Loguru',
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
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-[var(--app-elevated-bg)] backdrop-blur-md border-b border-[var(--app-border-color)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="text-xl font-bold tracking-tight">
            <span className="text-blue-500">Full</span>Stack
            <span className="text-[var(--app-text-secondary)] text-sm ml-2">Template</span>
          </div>
          {isAuthenticated ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
              <Avatar
                icon={<UserOutlined />}
                style={{ background: '#1668dc', cursor: 'pointer' }}
              />
            </Dropdown>
          ) : (
            <Button
              type="primary"
              size="small"
              onClick={() => navigate('/login')}
            >
              登录
            </Button>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <Tag color="blue" className="mb-4">🚀 开箱即用的全栈模板</Tag>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
            快速启动你的
            <span className="text-blue-500"> 全栈项目</span>
          </h1>
          <p className="text-lg sm:text-xl text-[var(--app-text-secondary)] max-w-2xl mx-auto mb-8 leading-relaxed">
            基于 FastAPI + React 19 的现代化全栈模板，
            内置完整认证系统、主题切换和模块化架构，
            让你专注于业务逻辑开发。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <Button
                type="primary"
                size="large"
                className="h-12 px-8 text-base font-medium"
                onClick={() => navigate('/dashboard')}
              >
                进入工作台
              </Button>
            ) : (
              <>
                <Button
                  type="primary"
                  size="large"
                  className="h-12 px-8 text-base font-medium"
                  onClick={() => navigate('/register')}
                >
                  免费开始使用
                </Button>
                <Button
                  size="large"
                  className="h-12 px-8 text-base font-medium"
                  onClick={() => navigate('/login')}
                >
                  已有账号？登录
                </Button>
              </>
            )}
          </div>
          {!isAuthenticated && (
            <p className="mt-4 text-sm text-[var(--app-text-secondary)]">
              无需信用卡 · 开源免费 · 即刻部署
            </p>
          )}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 border-y border-[var(--app-border-color)]">
        <div className="max-w-7xl mx-auto">
          <p className="text-center text-sm text-[var(--app-text-secondary)] mb-6 uppercase tracking-wider">
            技术栈
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {techStack.map((tech) => (
              <Tag key={tech} className="text-sm py-1 px-3">
                {tech}
              </Tag>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              为什么选择这个模板？
            </h2>
            <p className="text-lg text-[var(--app-text-secondary)] max-w-2xl mx-auto">
              经过实战验证的架构设计，助你快速构建生产级应用
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-2xl bg-[var(--app-elevated-bg)] border border-[var(--app-border-color)] theme-card-shadow hover:translate-y-[-4px] transition-all duration-300"
              >
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-[var(--app-text-secondary)] leading-relaxed">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="p-10 sm:p-16 rounded-3xl bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-cyan-500/10 border border-[var(--app-border-color)]">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              {isAuthenticated ? '继续你的开发之旅？' : '准备好开始了吗？'}
            </h2>
            <p className="text-lg text-[var(--app-text-secondary)] mb-8 max-w-xl mx-auto">
              {isAuthenticated
                ? '回到工作台，继续构建你的应用'
                : '加入开发者社区，使用这个经过验证的全栈模板启动你的下一个项目'}
            </p>
            <Button
              type="primary"
              size="large"
              className="h-12 px-8 text-base font-medium"
              onClick={() => navigate(isAuthenticated ? '/dashboard' : '/register')}
            >
              {isAuthenticated ? '进入工作台' : '立即注册，免费使用'}
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-[var(--app-border-color)]">
        <div className="max-w-7xl mx-auto text-center text-sm text-[var(--app-text-secondary)]">
          <p>© 2026 FullStack Template. 开源项目，MIT 许可证。</p>
        </div>
      </footer>
    </div>
  )
}
