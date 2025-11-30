import { create } from 'zustand'

export const useThemeStore = create((set) => ({
  isDark: localStorage.getItem('theme') === 'dark',

  toggleDarkMode: () =>
    set((state) => {
      const newDark = !state.isDark
      localStorage.setItem('theme', newDark ? 'dark' : 'light')
      if (newDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      return { isDark: newDark }
    }),

  initTheme: () => {
    const isDark = localStorage.getItem('theme') === 'dark'
    if (isDark) {
      document.documentElement.classList.add('dark')
    }
    set({ isDark })
  },
}))
