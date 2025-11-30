import { useThemeStore } from '../stores/themeStore'

export default function DarkModeToggle() {
  const { isDark, toggleDarkMode } = useThemeStore()

  return (
    <button
      onClick={toggleDarkMode}
      className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? '☀️' : '🌙'}
    </button>
  )
}
