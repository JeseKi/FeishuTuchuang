import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import DashboardPage from './pages/dashboard/DashboardPage'
import ImageHostPage from './pages/dashboard/ImageHostPage'
import ProfilePage from './pages/profile/ProfilePage'
import SecurityPage from './pages/profile/SecurityPage'
import DevicesPage from './pages/profile/DevicesPage'
import AdminManagementPage from './pages/admin/AdminManagementPage'
import LoginPage from './pages/auth/LoginPage'
import ConfirmPasswordChangePage from './pages/auth/ConfirmPasswordChangePage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import LandingPage from './pages/landing/LandingPage'
import { AuthProvider, RequireAdmin, RequireAuth } from './providers/AuthProvider'
import { RuntimeConfigProvider } from './providers/RuntimeConfigProvider'
import ThemeToggle from './components/theme/ThemeToggle'

export default function App() {
  return (
    <Router>
      <RuntimeConfigProvider>
        <AuthProvider>
          <>
            <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
            <Route path="/profile/password-change/:token" element={<ConfirmPasswordChangePage />} />
            <Route
              element={
                <RequireAuth>
                  <MainLayout />
                </RequireAuth>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/images" element={<ImageHostPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/profile/security" element={<SecurityPage />} />
              <Route path="/profile/devices" element={<DevicesPage />} />
              <Route
                path="/admin"
                element={
                  <RequireAdmin>
                    <AdminManagementPage />
                  </RequireAdmin>
                }
              />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <ThemeToggle />
          </>
        </AuthProvider>
      </RuntimeConfigProvider>
    </Router>
  )
}
