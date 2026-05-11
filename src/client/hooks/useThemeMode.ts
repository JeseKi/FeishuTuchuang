import { useContext } from 'react'
import { ThemeContext } from '../contexts/ThemeContext'

export function useThemeMode() {
  const context = useContext(ThemeContext)

  if (!context) {
    throw new Error('useThemeMode must be used within a ThemeProvider')
  }

  return context
}
