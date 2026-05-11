import { Alert, Button, Card, Result, Space, Statistic, Typography } from 'antd'
import { ThunderboltOutlined } from '@ant-design/icons'
import type { ThemeConfig } from 'antd'

interface HealthCheckCardProps {
  pingLoading: boolean
  pingError: string | null
  pingResult: string | null
  statisticValue: string
  token: ThemeConfig['token']
  onPing: () => void
}

export default function HealthCheckCard({
  pingLoading,
  pingError,
  pingResult,
  statisticValue,
  token,
  onPing,
}: HealthCheckCardProps) {
  return (
    <Card
      title="服务健康监控"
      extra={
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          loading={pingLoading}
          onClick={onPing}
        >
          {pingLoading ? '检测中' : '发起检测'}
        </Button>
      }
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Typography.Paragraph type="secondary">
          这里会调用后端的 ping 接口，确认服务是否正常运行，并同步展示最新状态。
        </Typography.Paragraph>
        <Statistic
          title="当前服务状态"
          value={statisticValue}
          valueStyle={{ color: statisticValue === '异常' ? token?.colorError : token?.colorPrimary }}
        />
        {pingError && <Alert type="error" showIcon message={pingError} />}
        {!pingError && pingResult && (
          <Result
            status="success"
            title={pingResult}
            subTitle="后端服务已成功响应请求。"
          />
        )}
        {!pingError && !pingResult && (
          <Alert type="info" showIcon message="尚未发起检测，请点击上方按钮。" />
        )}
      </Space>
    </Card>
  )
}
