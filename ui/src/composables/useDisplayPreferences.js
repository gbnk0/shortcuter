import { ref } from 'vue'

const COMPACT_KEY = 'shortcuter-compact-view'

export function useDisplayPreferences() {
  const compactView = ref(localStorage.getItem(COMPACT_KEY) === 'true')

  function applyDefaultDisplayDensity(displayDensity) {
    if (localStorage.getItem(COMPACT_KEY) !== null) {
      return
    }
    compactView.value = displayDensity === 'compact'
  }

  function toggleCompactView() {
    compactView.value = !compactView.value
    localStorage.setItem(COMPACT_KEY, String(compactView.value))
  }

  return {
    applyDefaultDisplayDensity,
    compactView,
    toggleCompactView,
  }
}
