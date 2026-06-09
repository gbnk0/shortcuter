import { computed, ref } from 'vue'

const COMPACT_KEY = 'shortcuter-compact-view'

export function useDisplayPreferences() {
  const compactView = ref(localStorage.getItem(COMPACT_KEY) === 'true')
  const compactTitle = computed(() => (compactView.value ? 'Comfortable view' : 'Compact view'))

  function toggleCompactView() {
    compactView.value = !compactView.value
    localStorage.setItem(COMPACT_KEY, String(compactView.value))
  }

  return {
    compactTitle,
    compactView,
    toggleCompactView,
  }
}
