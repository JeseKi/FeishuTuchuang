import { type ReactNode, useEffect, useMemo, useState } from 'react'
import {
  RuntimeConfigContext,
  type RuntimeConfigValue,
  type TurnstileRuntimeConfig,
} from '../contexts/RuntimeConfigContext'
import { fetchDevFrontendConfig } from '../lib/runtimeConfig'

const fallbackTurnstileConfig: TurnstileRuntimeConfig = {
  enabled: Boolean((import.meta.env.VITE_TURNSTILE_SITE_KEY ?? '').trim()),
  siteKey: (import.meta.env.VITE_TURNSTILE_SITE_KEY ?? '').trim(),
}

export function RuntimeConfigProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [turnstile, setTurnstile] = useState<TurnstileRuntimeConfig>(fallbackTurnstileConfig)

  useEffect(() => {
    let alive = true

    const load = async () => {
      try {
        const config = await fetchDevFrontendConfig()
        const devTurnstile = config?.turnstile
        if (!alive || !devTurnstile) {
          return
        }

        const siteKey = (devTurnstile.site_key ?? '').trim() || fallbackTurnstileConfig.siteKey
        const scriptUrl = (devTurnstile.script_url ?? '').trim() || undefined
        setTurnstile({
          enabled: Boolean(devTurnstile.enabled && siteKey),
          siteKey,
          scriptUrl,
        })
      } finally {
        if (alive) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      alive = false
    }
  }, [])

  const value = useMemo<RuntimeConfigValue>(
    () => ({
      loading,
      turnstile,
    }),
    [loading, turnstile],
  )

  return (
    <RuntimeConfigContext.Provider value={value}>
      {children}
    </RuntimeConfigContext.Provider>
  )
}
