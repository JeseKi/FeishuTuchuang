import { App as AntdApp, ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from '../../App'
import { useThemeMode } from '../../hooks/useThemeMode'

export default function ThemedApp() {
  const { resolvedTheme } = useThemeMode()
  const isDark = resolvedTheme === 'dark'

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: isDark ? '#60a5fa' : '#1668dc',
          borderRadius: 8,
          colorBgBase: isDark ? '#0f172a' : '#ffffff',
          colorBgLayout: isDark ? '#0b1220' : '#f5f7fb',
          colorTextBase: isDark ? '#e5eefc' : '#111827',
          fontFamily:
            "'Inter', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', system-ui, -apple-system, sans-serif",
        },
        components: {
          Button: {
            controlHeight: 40,
            fontWeight: 600,
            paddingInline: 16,
          },
          Layout: {
            headerBg: isDark ? '#101826' : '#ffffff',
            bodyBg: 'transparent',
          },
          Card: {
            borderRadiusLG: 12,
          },
        },
      }}
    >
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  )
}
