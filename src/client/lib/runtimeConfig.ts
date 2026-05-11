import api from './api'

interface DevFrontendConfigResponse {
  turnstile?: {
    enabled?: boolean
    site_key?: string
    script_url?: string
  }
}

export async function fetchDevFrontendConfig(): Promise<DevFrontendConfigResponse | null> {
  try {
    const response = await api.get<DevFrontendConfigResponse>('/dev/providers/frontend-config')
    return response.data
  } catch {
    return null
  }
}
