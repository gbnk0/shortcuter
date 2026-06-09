import { computed, ref } from 'vue'

const COMPACT_KEY = 'shortcuter-compact-view'
const FAVORITES_KEY = 'shortcuter-favorite-shortcuts'

function readJson(key, fallback) {
  try {
    const value = localStorage.getItem(key)
    return value ? JSON.parse(value) : fallback
  } catch {
    return fallback
  }
}

export function useDisplayPreferences() {
  const compactView = ref(localStorage.getItem(COMPACT_KEY) === 'true')
  const favoriteIds = ref(readJson(FAVORITES_KEY, []))
  const favoriteSet = computed(() => new Set(favoriteIds.value))
  const compactTitle = computed(() => (compactView.value ? 'Comfortable view' : 'Compact view'))

  function persistFavorites() {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favoriteIds.value))
  }

  function toggleCompactView() {
    compactView.value = !compactView.value
    localStorage.setItem(COMPACT_KEY, String(compactView.value))
  }

  function toggleFavorite(shortcutId) {
    if (favoriteSet.value.has(shortcutId)) {
      favoriteIds.value = favoriteIds.value.filter((id) => id !== shortcutId)
    } else {
      favoriteIds.value = [...favoriteIds.value, shortcutId]
    }
    persistFavorites()
  }

  return {
    compactTitle,
    compactView,
    favoriteIds,
    favoriteSet,
    toggleCompactView,
    toggleFavorite,
  }
}
