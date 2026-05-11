import { createContext } from 'react'

export interface TurnstileRuntimeConfig {
  enabled: boolean
  siteKey: string
  scriptUrl?: string
}

export interface RuntimeConfigValue {
  loading: boolean
  turnstile: TurnstileRuntimeConfig
}

const RuntimeConfigContext = createContext<RuntimeConfigValue | undefined>(undefined)

export { RuntimeConfigContext }
