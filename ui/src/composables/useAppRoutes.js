import { computed, onUnmounted, ref } from 'vue'

export function useAppRoutes(defaultPageId = 'general') {
  const currentPath = ref(window.location.pathname)
  const lastShortcutPage = ref(defaultPageId)
  const activeView = computed(() => (currentPath.value === '/icons' ? 'icons' : 'shortcuts'))
  const activePage = computed(() => {
    if (currentPath.value === '/icons') {
      return lastShortcutPage.value
    }
    const match = currentPath.value.match(/^\/page\/([^/]+)$/)
    if (match?.[1]) {
      return decodeURIComponent(match[1])
    }
    return defaultPageId
  })

  function syncPath() {
    currentPath.value = window.location.pathname
  }

  function pushRoute(nextPath) {
    window.history.pushState({}, '', nextPath)
    syncPath()
  }

  function replaceRoute(nextPath) {
    window.history.replaceState({}, '', nextPath)
    syncPath()
  }

  function selectPage(pageId) {
    lastShortcutPage.value = pageId
    pushRoute(`/page/${pageId}`)
  }

  function toggleIconsView() {
    if (activeView.value === 'icons') {
      pushRoute(`/page/${activePage.value}`)
      return
    }
    pushRoute('/icons')
  }

  function initRoutes() {
    window.addEventListener('popstate', syncPath)
  }

  onUnmounted(() => {
    window.removeEventListener('popstate', syncPath)
  })

  return {
    activePage,
    activeView,
    currentPath,
    lastShortcutPage,
    initRoutes,
    replaceRoute,
    selectPage,
    toggleIconsView,
  }
}

