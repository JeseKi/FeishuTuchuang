import { useEffect, useRef } from 'react'

const TURNSTILE_SCRIPT_ID = 'cf-turnstile-api'
const DEFAULT_TURNSTILE_SCRIPT_URL = 'https://challenges.cloudflare.com/turnstile/v0/api.js'

type TurnstileWidgetId = string | number

interface CloudflareTurnstileApi {
  render: (
    container: Element | string,
    options: Record<string, unknown>,
  ) => TurnstileWidgetId
  remove: (widgetId: TurnstileWidgetId) => void
  reset: (widgetId: TurnstileWidgetId) => void
}

declare global {
  interface Window {
    turnstile?: CloudflareTurnstileApi
  }
}

interface TurnstileWidgetProps {
  siteKey: string
  action?: string
  onToken: (token: string | null) => void
  onError?: () => void
  onExpire?: () => void
  className?: string
  scriptUrl?: string
  theme?: 'light' | 'dark' | 'auto'
}

export default function TurnstileWidget({
  siteKey,
  action,
  onToken,
  onError,
  onExpire,
  className,
  scriptUrl = DEFAULT_TURNSTILE_SCRIPT_URL,
  theme = 'auto',
}: TurnstileWidgetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const widgetIdRef = useRef<TurnstileWidgetId | null>(null)
  const onTokenRef = useRef(onToken)
  const onErrorRef = useRef(onError)
  const onExpireRef = useRef(onExpire)

  onTokenRef.current = onToken
  onErrorRef.current = onError
  onExpireRef.current = onExpire

  useEffect(() => {
    if (!siteKey || !containerRef.current) {
      return
    }

    const container = containerRef.current

    const renderWidget = () => {
      if (!window.turnstile || widgetIdRef.current) {
        return
      }

      const widgetId = window.turnstile.render(container, {
        sitekey: siteKey,
        action,
        theme,
        callback: (token: string): void => {
          onTokenRef.current(token)
        },
        'expired-callback': (): void => {
          onTokenRef.current(null)
          if (onExpireRef.current) {
            onExpireRef.current()
          }
        },
        'error-callback': (): void => {
          onTokenRef.current(null)
          if (onErrorRef.current) {
            onErrorRef.current()
          }
        },
      })

      widgetIdRef.current = widgetId
    }

    const existing = document.getElementById(TURNSTILE_SCRIPT_ID)
    if (window.turnstile) {
      renderWidget()
    } else if (existing) {
      const handleLoad = () => {
        renderWidget()
      }
      existing.addEventListener('load', handleLoad, { once: true })
    } else {
      const script = document.createElement('script')
      script.id = TURNSTILE_SCRIPT_ID
      script.src = scriptUrl
      script.async = true
      script.defer = true
      script.addEventListener('load', () => {
        renderWidget()
      }, { once: true })
      document.head.appendChild(script)
    }

    return () => {
      const widgetId = widgetIdRef.current
      if (widgetId !== null && window.turnstile) {
        window.turnstile.remove(widgetId)
      }
      widgetIdRef.current = null
      onTokenRef.current(null)
    }
  }, [action, scriptUrl, siteKey, theme])

  return <div ref={containerRef} className={className} />
}
