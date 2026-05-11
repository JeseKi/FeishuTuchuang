import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import type {
  BackupCodesResponse,
  EmailChangeCodePayload,
  EmailChangeConfirmPayload,
  LoginPayload,
  MessageResponse,
  OAuthTicketExchangePayload,
  PasswordChangeConfirmPayload,
  PasswordResetLinkPayload,
  PasswordResetWithTokenPayload,
  RegisterWithCodePayload,
  TwoFactorDisablePayload,
  TwoFactorRegenerateBackupCodesPayload,
  TwoFactorSetupConfirmPayload,
  TwoFactorSetupStartResponse,
  TwoFactorVerifyPayload,
  UpdateProfilePayload,
  UserProfile,
  VerificationCodePayload,
} from '../lib/types'
import { hasValidTokens } from '../lib/tokenStorage'
import {
  clearAuthState,
  confirmTwoFactorSetup as confirmTwoFactorSetupRequest,
  confirmEmailChange,
  confirmPasswordChange,
  disableTwoFactor as disableTwoFactorRequest,
  fetchProfile,
  exchangeOAuthTicket as exchangeOAuthTicketRequest,
  login as loginRequest,
  logout as logoutRequest,
  logoutAllDevices as logoutAllDevicesRequest,
  regenerateBackupCodes as regenerateBackupCodesRequest,
  register as registerRequest,
  registerWithCode as registerWithCodeRequest,
  resetPasswordWithToken as resetPasswordWithTokenRequest,
  sendEmailChangeCode as sendEmailChangeCodeRequest,
  sendPasswordChangeLink as sendPasswordChangeLinkRequest,
  sendPasswordResetLink as sendPasswordResetLinkRequest,
  sendVerificationCode as sendVerificationCodeRequest,
  startTwoFactorSetup as startTwoFactorSetupRequest,
  updateProfile,
  verifyTwoFactorLogin as verifyTwoFactorLoginRequest,
} from '../lib/auth'
import { useAuth } from '../hooks/useAuth'
import { AuthContext, type AuthContextValue } from '../contexts/AuthContext'


export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const bootstrap = async () => {
      if (!hasValidTokens()) {
        setLoading(false)
        return
      }
      try {
        const profile = await fetchProfile()
        setUser(profile)
      } catch (error) {
        console.log(error)
        clearAuthState()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    void bootstrap()
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    const result = await loginRequest(payload)
    if ('requires_2fa' in result) {
      return result
    }
    const profile = await fetchProfile()
    setUser(profile)
    return result
  }, [])

  const exchangeOAuthTicket = useCallback(async (payload: OAuthTicketExchangePayload) => {
    const result = await exchangeOAuthTicketRequest(payload)
    if ('requires_2fa' in result) {
      return result
    }
    const profile = await fetchProfile()
    setUser(profile)
    return result
  }, [])

  const verifyTwoFactorLogin = useCallback(async (payload: TwoFactorVerifyPayload) => {
    await verifyTwoFactorLoginRequest(payload)
    const profile = await fetchProfile()
    setUser(profile)
    return profile
  }, [])

  const register = useCallback(async (payload: RegisterWithCodePayload) => {
    const profile = await registerRequest(payload)
    return profile
  }, [])

  const registerWithCode = useCallback(async (payload: RegisterWithCodePayload) => {
    const profile = await registerWithCodeRequest(payload)
    return profile
  }, [])

  const sendVerificationCode = useCallback(async (payload: VerificationCodePayload) => {
    const result = await sendVerificationCodeRequest(payload)
    return result
  }, [])

  const sendPasswordResetLink = useCallback(async (payload: PasswordResetLinkPayload) => {
    const result = await sendPasswordResetLinkRequest(payload)
    return result
  }, [])

  const refreshProfile = useCallback(async () => {
    if (!hasValidTokens()) {
      setUser(null)
      return null
    }
    try {
      const profile = await fetchProfile()
      setUser(profile)
      return profile
    } catch (error) {
      clearAuthState()
      setUser(null)
      throw error
    }
  }, [])

  const logout = useCallback(async () => {
    await logoutRequest()
    setUser(null)
  }, [])

  const logoutAllDevices = useCallback(async () => {
    const result = await logoutAllDevicesRequest()
    setUser(null)
    return result
  }, [])

  const startTwoFactorSetup = useCallback(async (): Promise<TwoFactorSetupStartResponse> => {
    const result = await startTwoFactorSetupRequest()
    return result
  }, [])

  const confirmTwoFactorSetup = useCallback(
    async (payload: TwoFactorSetupConfirmPayload): Promise<BackupCodesResponse> => {
      const result = await confirmTwoFactorSetupRequest(payload)
      const profile = await fetchProfile()
      setUser(profile)
      return result
    },
    [],
  )

  const disableTwoFactor = useCallback(
    async (payload: TwoFactorDisablePayload): Promise<MessageResponse> => {
      const result = await disableTwoFactorRequest(payload)
      setUser(null)
      return result
    },
    [],
  )

  const regenerateBackupCodes = useCallback(
    async (payload: TwoFactorRegenerateBackupCodesPayload): Promise<BackupCodesResponse> => {
      const result = await regenerateBackupCodesRequest(payload)
      return result
    },
    [],
  )

  const handleUpdate = useCallback(async (payload: UpdateProfilePayload) => {
    const updated = await updateProfile(payload)
    setUser(updated)
    return updated
  }, [])

  const handleResetPassword = useCallback(
    async (payload: PasswordResetWithTokenPayload) => {
      const result = await resetPasswordWithTokenRequest(payload)
      return result
    },
    [],
  )

  const handleSendEmailChangeCode = useCallback(async (payload: EmailChangeCodePayload) => {
    const result = await sendEmailChangeCodeRequest(payload)
    return result
  }, [])

  const handleConfirmEmailChange = useCallback(async (payload: EmailChangeConfirmPayload) => {
    const updated = await confirmEmailChange(payload)
    setUser(updated)
    return updated
  }, [])

  const handleSendPasswordChangeLink = useCallback(async (twoFactorCode?: string) => {
    const result = await sendPasswordChangeLinkRequest(twoFactorCode)
    return result
  }, [])

  const handleConfirmPasswordChange = useCallback(async (payload: PasswordChangeConfirmPayload) => {
    const result = await confirmPasswordChange(payload)
    return result
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      exchangeOAuthTicket,
      verifyTwoFactorLogin,
      register,
      registerWithCode,
      sendVerificationCode,
      sendPasswordResetLink,
      sendEmailChangeCode: handleSendEmailChangeCode,
      confirmEmailChange: handleConfirmEmailChange,
      sendPasswordChangeLink: handleSendPasswordChangeLink,
      confirmPasswordChange: handleConfirmPasswordChange,
      refreshProfile,
      logout,
      logoutAllDevices,
      startTwoFactorSetup,
      confirmTwoFactorSetup,
      disableTwoFactor,
      regenerateBackupCodes,
      update: handleUpdate,
      resetPasswordWithToken: handleResetPassword,
    }),
    [
      user,
      loading,
      login,
      exchangeOAuthTicket,
      verifyTwoFactorLogin,
      register,
      registerWithCode,
      sendVerificationCode,
      sendPasswordResetLink,
      handleSendEmailChangeCode,
      handleConfirmEmailChange,
      handleSendPasswordChangeLink,
      handleConfirmPasswordChange,
      refreshProfile,
      logout,
      logoutAllDevices,
      startTwoFactorSetup,
      confirmTwoFactorSetup,
      disableTwoFactor,
      regenerateBackupCodes,
      handleUpdate,
      handleResetPassword,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="theme-loading-text flex h-screen items-center justify-center">
        正在验证登录状态...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading, user } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="theme-loading-text flex h-screen items-center justify-center">
        正在验证登录状态...
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (user?.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
