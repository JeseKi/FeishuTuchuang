import {
  DesktopOutlined,
  MoonOutlined,
  SunOutlined,
} from '@ant-design/icons'
import { Button, Flex, Popover, Segmented, Space, Typography } from 'antd'
import {
  type ResolvedTheme,
  type ThemePreference,
} from '../../contexts/ThemeContext'
import { useThemeMode } from '../../hooks/useThemeMode'

function resolveThemeIcon(theme: ResolvedTheme) {
  return theme === 'dark' ? <MoonOutlined /> : <SunOutlined />
}

function resolveThemeLabel(theme: ThemePreference) {
  if (theme === 'system') {
    return '跟随系统'
  }
  return theme === 'dark' ? '夜间模式' : '浅色模式'
}

export default function ThemeToggle() {
  const { preference, resolvedTheme, setPreference } = useThemeMode()

  return (
    <div
      style={{
        position: 'fixed',
        right: 24,
        bottom: 24,
        zIndex: 1100,
      }}
    >
      <Popover
        trigger="click"
        placement="topRight"
        content={(
          <Flex vertical gap={12} style={{ minWidth: 220 }}>
            <Space direction="vertical" size={2}>
              <Typography.Text strong>界面主题</Typography.Text>
              <Typography.Text type="secondary">
                当前为{resolvedTheme === 'dark' ? '夜间模式' : '浅色模式'}
              </Typography.Text>
            </Space>
            <Segmented<ThemePreference>
              block
              value={preference}
              onChange={(value) => setPreference(value)}
              options={[
                {
                  label: (
                    <Space size={6}>
                      <DesktopOutlined />
                      <span>系统</span>
                    </Space>
                  ),
                  value: 'system',
                },
                {
                  label: (
                    <Space size={6}>
                      <SunOutlined />
                      <span>浅色</span>
                    </Space>
                  ),
                  value: 'light',
                },
                {
                  label: (
                    <Space size={6}>
                      <MoonOutlined />
                      <span>夜间</span>
                    </Space>
                  ),
                  value: 'dark',
                },
              ]}
            />
          </Flex>
        )}
      >
        <Button
          shape="circle"
          size="large"
          icon={resolveThemeIcon(resolvedTheme)}
          aria-label={resolveThemeLabel(preference)}
          title={resolveThemeLabel(preference)}
          style={{
            width: 48,
            height: 48,
            color: 'var(--app-text-primary)',
            background: 'var(--app-elevated-bg)',
            borderColor: 'var(--app-border-color)',
            boxShadow: 'var(--app-floating-shadow)',
          }}
        />
      </Popover>
    </div>
  )
}
