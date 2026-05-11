import { Alert, Button, Input, Space, Spin, Typography, theme } from 'antd'
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import {
  confirmOAuthDeviceAuthorization,
  fetchOAuthDeviceAuthorizationMetadata,
} from '../../lib/oauthProvider'
import type { OAuthDeviceAuthorizationMetadata } from '../../lib/types'

const { Paragraph, Text, Title } = Typography

function resolveErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const maybeResponse = error as { response?: { data?: { detail?: unknown } } }
    const detail = maybeResponse.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (typeof detail === 'object' && detail !== null && 'message' in detail) {
      const message = (detail as { message?: unknown }).message
      if (typeof message === 'string') return message
    }
  }
  return fallback
}

function normalizeUserCode(value: string): string {
  return value.toUpperCase().replace(/[^A-Z0-9]/g, '')
}

function formatExpiresAt(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString()
}

export default function OAuthDeviceAuthorizePage() {
  const location = useLocation()
  const { user } = useAuth()
  const { token } = theme.useToken()
  const queryUserCode = useMemo(() => new URLSearchParams(location.search).get('user_code') ?? '', [location.search])
  const [userCode, setUserCode] = useState(queryUserCode)
  const [metadata, setMetadata] = useState<OAuthDeviceAuthorizationMetadata | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [completedStatus, setCompletedStatus] = useState<'approved' | 'denied' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const normalizedUserCode = normalizeUserCode(userCode)
  const canLoadMetadata = normalizedUserCode.length >= 8

  const loadMetadata = async (value: string) => {
    setLoading(true)
    setError(null)
    setCompletedStatus(null)
    try {
      const result = await fetchOAuthDeviceAuthorizationMetadata(value)
      setMetadata(result)
      setUserCode(result.user_code)
    } catch (err) {
      setMetadata(null)
      setError(resolveErrorMessage(err, '授权码无效或已过期'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (queryUserCode) {
      void loadMetadata(queryUserCode)
    }
  }, [queryUserCode])

  const submitConsent = async (approve: boolean) => {
    setSubmitting(true)
    setError(null)
    try {
      const result = await confirmOAuthDeviceAuthorization({
        user_code: metadata?.user_code ?? userCode,
        approve,
      })
      setCompletedStatus(result.status)
      setMetadata(null)
    } catch (err) {
      setError(resolveErrorMessage(err, '授权失败'))
    } finally {
      setSubmitting(false)
    }
  }

  const resultContent = completedStatus ? (
    <div className="flex flex-col items-center justify-center gap-4 py-10 text-center">
      {completedStatus === 'approved' ? (
        <CheckCircleFilled style={{ fontSize: 96, color: token.colorSuccess }} />
      ) : (
        <CloseCircleFilled style={{ fontSize: 96, color: token.colorTextTertiary }} />
      )}
      <div>
        <Title level={3} style={{ marginBottom: token.marginXS }}>
          {completedStatus === 'approved' ? '授权成功' : '已拒绝授权'}
        </Title>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {completedStatus === 'approved' ? '设备现在可以继续完成登录。' : '设备无法继续访问你的账号。'}
        </Paragraph>
      </div>
    </div>
  ) : null

  return (
    <main
      className="flex min-h-screen items-center justify-center px-4 py-8"
      style={{ background: token.colorBgLayout }}
    >
      <section
        className="w-full max-w-xl rounded-md border p-6 shadow-sm"
        style={{ background: token.colorBgContainer, borderColor: token.colorBorderSecondary }}
      >
        <Space direction="vertical" size="large" className="w-full">
          <div>
            <Title level={3} style={{ marginBottom: token.marginXS }}>
              设备授权
            </Title>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              <Text strong>{user?.username}</Text>
              {user?.email && <Text type="secondary"> · {user.email}</Text>}
            </Paragraph>
          </div>

          {error && <Alert type="error" message={error} showIcon />}

          {resultContent}

          {!completedStatus && !metadata && (
            <Space.Compact className="w-full">
              <Input
                size="large"
                value={userCode}
                placeholder="ABCD-EFGH"
                maxLength={16}
                onChange={(event) => setUserCode(event.target.value.toUpperCase())}
                onPressEnter={() => {
                  if (canLoadMetadata) void loadMetadata(userCode)
                }}
              />
              <Button
                size="large"
                type="primary"
                loading={loading}
                disabled={!canLoadMetadata}
                onClick={() => void loadMetadata(userCode)}
              >
                继续
              </Button>
            </Space.Compact>
          )}

          {!completedStatus && loading && (
            <div className="flex justify-center py-6">
              <Spin />
            </div>
          )}

          {!completedStatus && metadata && (
            <Space direction="vertical" size="middle" className="w-full">
              <div>
                <Text type="secondary">请求授权的设备</Text>
                <div>
                  <Text strong>{metadata.client_name}</Text>
                </div>
              </div>

              <div>
                <Text type="secondary">授权码</Text>
                <div>
                  <Text strong>{metadata.user_code}</Text>
                </div>
              </div>

              <div>
                <Text type="secondary">对方应用将可以</Text>
                <div className="mt-2 flex flex-col gap-2">
                  {metadata.permissions.length > 0 ? (
                    metadata.permissions.map((permission) => (
                      <div
                        key={permission.scope}
                        className="rounded-md border px-3 py-2"
                        style={{ borderColor: token.colorBorderSecondary, background: token.colorFillAlter }}
                      >
                        <Text strong>{permission.title}</Text>
                        <div>
                          <Text type="secondary">{permission.description}</Text>
                        </div>
                      </div>
                    ))
                  ) : (
                    <Text>仅确认你的登录身份，不读取额外信息。</Text>
                  )}
                </div>
              </div>

              <div>
                <Text type="secondary">有效期至</Text>
                <div>
                  <Text>{formatExpiresAt(metadata.expires_at)}</Text>
                </div>
              </div>

              <Space className="w-full justify-end">
                <Button disabled={submitting} onClick={() => void submitConsent(false)}>
                  不允许
                </Button>
                <Button type="primary" loading={submitting} onClick={() => void submitConsent(true)}>
                  允许
                </Button>
              </Space>
            </Space>
          )}
        </Space>
      </section>
    </main>
  )
}
