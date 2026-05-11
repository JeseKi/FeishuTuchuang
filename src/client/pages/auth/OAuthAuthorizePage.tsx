import { Alert, Button, Space, Spin, Typography, theme } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { confirmOAuthAuthorize, fetchOAuthAuthorizeMetadata } from '../../lib/oauthProvider'
import type { OAuthAuthorizeMetadata } from '../../lib/types'

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

function formatRedirectHost(redirectUri: string): string {
  try {
    const url = new URL(redirectUri)
    return url.host
  } catch {
    return redirectUri
  }
}

export default function OAuthAuthorizePage() {
  const location = useLocation()
  const { user } = useAuth()
  const { token } = theme.useToken()
  const [metadata, setMetadata] = useState<OAuthAuthorizeMetadata | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const params = useMemo(() => new URLSearchParams(location.search), [location.search])

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    fetchOAuthAuthorizeMetadata(params)
      .then((result) => {
        if (alive) setMetadata(result)
      })
      .catch((err) => {
        if (alive) setError(resolveErrorMessage(err, '授权请求无效'))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [params])

  const submitConsent = async (approve: boolean) => {
    setSubmitting(true)
    setError(null)
    try {
      const result = await confirmOAuthAuthorize({
        response_type: params.get('response_type') ?? '',
        client_id: params.get('client_id') ?? '',
        redirect_uri: params.get('redirect_uri') ?? '',
        scope: params.get('scope') ?? '',
        state: params.get('state'),
        code_challenge: params.get('code_challenge') ?? '',
        code_challenge_method: params.get('code_challenge_method') ?? 'S256',
        approve,
      })
      window.location.assign(result.redirect_url)
    } catch (err) {
      setError(resolveErrorMessage(err, '授权失败'))
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spin />
      </div>
    )
  }

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
              允许访问你的账号？
            </Title>
            {metadata && (
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                <Text strong>{metadata.client_name}</Text> 想连接到你的账号。请确认它可以使用以下信息。
              </Paragraph>
            )}
          </div>

          {error && <Alert type="error" message={error} showIcon />}

          {metadata && (
            <Space direction="vertical" size="middle" className="w-full">
              <div>
                <Text type="secondary">你将使用的账号</Text>
                <div>
                  <Text strong>{user?.username}</Text>
                  {user?.email && <Text type="secondary"> · {user.email}</Text>}
                </div>
              </div>

              <div>
                <Text type="secondary">对方应用将可以</Text>
                <div className="mt-2 flex flex-col gap-2">
                  {metadata.permissions.length > 0 ? (
                    metadata.permissions.map((permission) => {
                      return (
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
                      )
                    })
                  ) : (
                    <Text>仅确认你的登录身份，不读取额外信息。</Text>
                  )}
                </div>
              </div>

              <div>
                <Text type="secondary">授权后将返回</Text>
                <div>
                  <Text strong>{formatRedirectHost(metadata.redirect_uri)}</Text>
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
