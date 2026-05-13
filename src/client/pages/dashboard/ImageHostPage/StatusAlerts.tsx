import { Alert } from 'antd'
import type { FeishuFolder, FeishuOAuthStatus } from '../../../lib/imageHost'

interface StatusAlertsProps {
  activeFolder: FeishuFolder | null
  error: string | null
  oauthStatus: FeishuOAuthStatus | null
  setError: (error: string | null) => void
}

export function StatusAlerts({
  activeFolder,
  error,
  oauthStatus,
  setError,
}: StatusAlertsProps) {
  return (
    <>
      {error && (
        <Alert type="error" showIcon message={error} closable onClose={() => setError(null)} />
      )}

      {oauthStatus && !oauthStatus.connected && (
        <Alert
          type="warning"
          showIcon
          message="尚未连接飞书 Drive，上传、回源和删除需要先完成飞书用户授权。"
        />
      )}

      {!activeFolder && (
        <Alert
          type="warning"
          showIcon
          message="尚未配置启用的飞书文件夹，上传会尝试使用飞书 Drive 根目录。"
        />
      )}
    </>
  )
}
