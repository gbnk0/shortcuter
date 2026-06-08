import { computed, ref } from 'vue'

export function useTheme() {
  const theme = ref('light')
  const themeTitle = computed(() => (theme.value === 'dark' ? 'Light theme' : 'Dark theme'))

  function applyTheme(nextTheme) {
    theme.value = nextTheme
    document.documentElement.dataset.theme = nextTheme
    localStorage.setItem('shortcuter-theme', nextTheme)
  }

  function toggleTheme() {
    applyTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  function initialTheme() {
    const savedTheme = localStorage.getItem('shortcuter-theme')
    if (savedTheme === 'dark' || savedTheme === 'light') {
      return savedTheme
    }
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  function initTheme() {
    applyTheme(initialTheme())
  }

  return {
    theme,
    themeTitle,
    initTheme,
    toggleTheme,
  }
}
